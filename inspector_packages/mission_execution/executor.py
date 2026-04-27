import time
import uuid
import subprocess
import sqlite3
import sys, os, shutil
import multiprocessing as mp
from pathlib import Path
from utils import cli_output, timer, WindowsFileAPI
from inspector_packages import np
import pandas as pd
from . import *

import pdb

class Executor:

   def __init__(self, mission_config, mission_output):

      pd.set_option('future.no_silent_downcasting', True)

      self._program_file = Path(sys.argv[0])
      self._mission_output = mission_output
      self._mission_config = mission_config
      self._startup_file = Path(self._mission_config["scenario_startup"])
      self._output_dir = self._program_file.parent.joinpath("output")
      self._db_conn = None
      self._uuid = uuid.uuid4()
      self._rows_per_file = 100000

      self._file_names = {
         "COMM": "comms_analysis",
      }
      self._file_num = 1

      self._required_events = [
         f"enable SIMULATION_STARTING SetupParameters_{self._uuid.hex}",
         f"enable SIMULATION_COMPLETE FinishVisualization_{self._uuid.hex}"]

      self._message_events = {
         AFSIMCommEvents.MESSAGE_OUTGOING: f"enable {AFSIMCommEvents.MESSAGE_OUTGOING} MessageOutgoing_{self._uuid.hex}",
         AFSIMCommEvents.MESSAGE_INCOMING: f"enable {AFSIMCommEvents.MESSAGE_INCOMING} MessageIncoming_{self._uuid.hex}",
         AFSIMCommEvents.MESSAGE_INTERNAL: f"enable {AFSIMCommEvents.MESSAGE_INTERNAL} MessageInternal_{self._uuid.hex}",
         AFSIMCommEvents.MESSAGE_DELIVERY_ATTEMPT: f"enable {AFSIMCommEvents.MESSAGE_DELIVERY_ATTEMPT} MessageDeliveryAttempt_{self._uuid.hex}",
         AFSIMCommEvents.MESSAGE_DISCARDED: f"enable {AFSIMCommEvents.MESSAGE_DISCARDED} MessageDiscarded_{self._uuid.hex}",
         AFSIMCommEvents.MESSAGE_FAILED_ROUTING: f"enable {AFSIMCommEvents.MESSAGE_FAILED_ROUTING} MessageFailedRouting_{self._uuid.hex}",
         AFSIMCommEvents.MESSAGE_HOP: f"enable {AFSIMCommEvents.MESSAGE_HOP} MessageHop_{self._uuid.hex}",
         AFSIMCommEvents.MESSAGE_UPDATED: f"enable {AFSIMCommEvents.MESSAGE_UPDATED} MessageUpdated_{self._uuid.hex}",
         AFSIMCommEvents.MESSAGE_QUEUED: f"enable {AFSIMCommEvents.MESSAGE_QUEUED} MessageQueued_{self._uuid.hex}",
         AFSIMCommEvents.MESSAGE_RECEIVED: f"enable {AFSIMCommEvents.MESSAGE_RECEIVED} MessageReceived_{self._uuid.hex}",
         AFSIMCommEvents.MESSAGE_TRANSMITTED: f"enable {AFSIMCommEvents.MESSAGE_TRANSMITTED} MessageTransmitted_{self._uuid.hex}",
         AFSIMCommEvents.MESSAGE_TRANSMITTED_HEARTBEAT: f"enable {AFSIMCommEvents.MESSAGE_TRANSMITTED_HEARTBEAT} MessageTransmittedHeartbeat_{self._uuid.hex}",
         AFSIMCommEvents.MESSAGE_TRANSMIT_ENDED: f"enable {AFSIMCommEvents.MESSAGE_TRANSMIT_ENDED} MessageTransmitEnded_{self._uuid.hex}"
      }

   @property
   def database(self):
      return self._db_conn

   def get_afsim_data(self):

      if (self._mission_config["run_mission"]):
      
         self._run_and_store()

      self._retrieve_data()

   @timer
   def _run_and_store(self):

      exec_endpoint, collect_endpoint = mp.Pipe()
      executor_process = mp.Process(
         target=self._execute_mission,
         args=(exec_endpoint,),
         name="Mission Executor",
         daemon=True)

      collector_process = mp.Process(
         target=self._store_data,
         args=("COMM", collect_endpoint),
         name="Data Collector",
         daemon=True
      )
      executor_process.start()
      collector_process.start()
      executor_process.join()
      collector_process.join()

   def _execute_mission(self, exec_endpoint):

      try:
         current_process = mp.current_process()
         cli_output.WARNING(f"{current_process.name}:{current_process.pid}")

         executor_file = self._build_executor_file()
         self._collect_data(executor_file, exec_endpoint)

         comm_files = [f for f in self._startup_file.parent.glob(f'{self._file_names["COMM"]}*.csv')]
         exec_endpoint.send(f"{len(comm_files)}")
      except KeyboardInterrupt as e:
         cli_output.FATAL(f"{current_process.name} INTERRUPTED!")
      finally:
         exec_endpoint.close()
         os.remove(executor_file)

   def _store_data(self, file_name, collect_endpoint):

      try:
         mission_exec_started = collect_endpoint.recv()
         current_process = mp.current_process()
         cli_output.WARNING(f"{current_process.name}:{current_process.pid}")
         time.sleep(2)

         if not self._output_dir.exists():
            os.mkdir(self._output_dir)

         output_name = self._mission_config["output_name"]
         if not self._output_dir.joinpath(output_name).exists():
            os.mkdir(self._output_dir.joinpath(output_name))

         self._db_conn = sqlite3.connect(self._output_dir.joinpath(output_name, "database.db"))
         execution_result = self._store_in_database(file_name, collect_endpoint)
         if execution_result == "FAIL":
            shutil.rmtree(self._output_dir.joinpath(output_name))
         collect_endpoint.close()

      except KeyboardInterrupt as e:
         cli_output.FATAL(f"{current_process.name} INTERRUPTED!")

      finally:
         if self._db_conn is not None:
            self._db_conn.close()
         comm_files = [f for f in self._startup_file.parent.glob(f'{self._file_names[file_name]}*.csv')]
         for f in comm_files:
            while True:
               try:
                  os.remove(f)
                  break
               except PermissionError as e:
                  pass


   def _retrieve_data(self):

      try:
         output_name = self._mission_config["output_name"]
         db_dir = self._output_dir.joinpath(output_name, "database.db")
         self._db_conn = sqlite3.connect(db_dir, check_same_thread=False)
         self._check_database()
         pdb.set_trace()
      except sqlite3.OperationalError as e:
         cli_output.FATAL(f'{str(e).upper()}: {db_dir}')
         if self._output_dir.exists():
            datasets = [f'{idx+1} {result.name}' for idx, result in enumerate(self._output_dir.iterdir())]
            if len(datasets) > 0:
               data_list = "\n".join(datasets)
               cli_output.FATAL(f"The following datasets are available: \n{data_list}")
         sys.exit(1)

   def _store_in_database(self, data_type, collect_endpoint):

      cur = self._db_conn.cursor()
      file_path = self._startup_file.parent.joinpath(f"{self._file_names[data_type]}_{self._file_num}.csv")
      total_comm_files = np.Inf
      execution_result = None

      while self._file_num <= total_comm_files:
         try:

            if collect_endpoint.poll():
               execution_result = collect_endpoint.recv()
               if execution_result == "FAIL":
                  collect_endpoint.send("ACK")
                  cli_output.WARNING("Aborting data collection... ")
                  break
               else:
                  total_comm_files = int(execution_result)

            WindowsFileAPI.check_permission(str(file_path))
            df = pd.read_csv(file_path)\
               .replace(r'^\s*$', np.nan, regex=True)\
               .fillna(value=eval(f'{data_type}_SUBSTITUTIONS'))

            if self._file_num == 1:
               df.to_sql(eval(f'{data_type}_DATA_TABLE'), self._db_conn, if_exists='replace', index=False)
            else:
               df.to_sql(eval(f'{data_type}_DATA_TABLE'), self._db_conn, if_exists='append', index=False)

            cli_output.WARNING(f"{file_path} successfully read and stored in database.")
            self._file_num += 1
            file_path = self._startup_file.parent.joinpath(f"{self._file_names[data_type]}_{self._file_num}.csv")
         except FileNotFoundError as e:
            cli_output.WARNING(f"{str(e)}")
         except PermissionError as e:
            cli_output.WARNING(f"{str(e)}")
         except OSError as e:
            cli_output.WARNING(f"{str(e)}")
         time.sleep(2)

      cli_output.WARNING(f"Ending database storage...")
      self._db_conn.commit()
      cur.close()
      return execution_result

   def _check_database(self):

      cur = self._db_conn.cursor()
      try:
         comm_data_exists = cur.execute(f"SELECT EXISTS(SELECT 1 FROM {COMM_DATA_TABLE})").fetchone()[0]
         if not comm_data_exists:
            cli_output.FATAL("No comms data was collected during scenario execution... exiting!")
            cur.close()
            self._db_conn.close()
            shutil.rmtree(self._output_dir.joinpath(self._mission_config["output_name"]))
            sys.exit(1)
      except sqlite3.OperationalError as e:
         cli_output.FATAL("No comms table was created during scenario execution... exiting!")
         cur.close()
         self._db_conn.close()
         shutil.rmtree(self._output_dir.joinpath(self._mission_config["output_name"]))
         sys.exit(1)
      cur.close()


   def _get_observer_block(self):

      observer_block = "\n   ".join(["observer", *self._required_events])
      for key, enabled in self._mission_config["message_events"].items():
         if enabled:
            observer_block = "\n   ".join([observer_block, self._message_events[key]])
         else:
            observer_block = "\n   ".join([observer_block, "# " + self._message_events[key]])

      observer_block += "\nend_observer"
   
      return observer_block
   
   def _get_include_docs(self):

      include_doc = "include_once " + str(self._startup_file.absolute().as_posix()) + "\n"

      include_doc += "include_once " + self._program_file.parent.absolute().joinpath(
         "utils", "collector_files", "comm_detail_collector.txt").as_posix() + "\n"

      return include_doc

   def _set_defines(self):

      defines = ""
      defines += f"$define UUID {self._uuid.hex}" + "\n"
      defines += f'$define COMM_FILE_NAME "{self._file_names["COMM"]}"' + "\n"
      defines += f"$define ROWS_PER_FILE {self._rows_per_file}" + "\n"

      return defines
   
   def _build_executor_file(self):

      with open(self._program_file.parent.joinpath("utils", "collector_files", "isr_afsim_collector.txt"), "r") as collector:
         collector_string = collector.read()

      output_name = self._mission_config["output_name"]
      executor_file = self._program_file.parent.joinpath(output_name + ".afsim")

      with open(executor_file, "w") as f:
         f.write("\n".join([self._set_defines(), self._get_include_docs(), collector_string, self._get_observer_block()]))

      return executor_file
   
   def _collect_data(self, executor_file, exec_endpoint):

      try:
         cli_output.INFO(f"Running mission for {self._startup_file}...")
         exec_endpoint.send("START MISSION")
         mission_result = subprocess.run(
            [self._mission_config["mission_exe_path"], str(executor_file.absolute())], 
            cwd=str(self._startup_file.parent), capture_output=(not self._mission_output))

         if mission_result.returncode != 0:
            cli_output.FATAL("Mission execution error... exiting!")
            exec_endpoint.send("FAIL")
            ack = exec_endpoint.recv()
            exec_endpoint.close()
            os.remove(executor_file)
            sys.exit(1)

         cli_output.OK(f"Mission execution of {self._startup_file} successfully completed.")
         os.remove(executor_file)

      except (NotADirectoryError, FileNotFoundError) as e:
         cli_output.FATAL(f"Mission execution error: {e.strerror}... exiting!")
         exec_endpoint.send("FAIL")
         ack = exec_endpoint.recv()
         exec_endpoint.close()
         os.remove(executor_file)
         sys.exit(1)