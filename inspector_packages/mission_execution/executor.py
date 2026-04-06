import time
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

   def __init__(self, mission_config):

      pd.set_option('future.no_silent_downcasting', True)

      self._program_file = Path(sys.argv[0])
      self._mission_config = mission_config
      self._startup_file = Path(self._mission_config["scenario_startup"])
      self._output_dir = self._program_file.parent.joinpath("output")
      self._db_conn = None
      self._queue_info = None

      self._file_names = {
         "COMM": "comms_analysis",
      }
      self._file_num = 1

      self._required_events = [
         "enable SIMULATION_STARTING SetupParameters",
         "enable SIMULATION_COMPLETE FinishVisualization"]

      self._message_events = {
         "MESSAGE_OUTGOING": "enable MESSAGE_OUTGOING comm_MessageOutgoing",
         "MESSAGE_INCOMING": "enable MESSAGE_INCOMING comm_MessageIncoming",
         "MESSAGE_INTERNAL": "enable MESSAGE_INTERNAL comm_MessageInternal",
         "MESSAGE_DELIVERY_ATTEMPT": "enable MESSAGE_DELIVERY_ATTEMPT comm_MessageDeliveryAttempt",
         "MESSAGE_DISCARDED": "enable MESSAGE_DISCARDED comm_MessageDiscarded",
         "MESSAGE_FAILED_ROUTING": "enable MESSAGE_FAILED_ROUTING comm_MessageFailedRouting",
         "MESSAGE_HOP": "enable MESSAGE_HOP comm_MessageHop",
         "MESSAGE_UPDATED": "enable MESSAGE_UPDATED comm_MessageUpdated",
         "MESSAGE_QUEUED": "enable MESSAGE_QUEUED comm_MessageQueued",
         "MESSAGE_RECEIVED": "enable MESSAGE_RECEIVED comm_MessageReceived",
         "MESSAGE_TRANSMITTED": "enable MESSAGE_TRANSMITTED comm_MessageTransmitted",
         "MESSAGE_TRANSMITTED_HEARTBEAT": "enable MESSAGE_TRANSMITTED_HEARTBEAT comm_MessageTransmittedHeartbeat",
         "MESSAGE_TRANSMIT_ENDED": "enable MESSAGE_TRANSMIT_ENDED comm_MessageTransmitEnded"
      }

   @property
   def database(self):
      return self._db_conn

   @property
   def queue_info(self):
      return self._queue_info

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
         exec_endpoint.close()
      except KeyboardInterrupt as e:
         cli_output.FATAL(f"{current_process.name} INTERRUPTED!")
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
         self._db_conn.close()
         if execution_result == "FAIL":
            shutil.rmtree(self._output_dir.joinpath(output_name))
         collect_endpoint.close()

      except KeyboardInterrupt as e:
         cli_output.FATAL(f"{current_process.name} INTERRUPTED!")

      finally:
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
               # cur.execute(f"DROP TABLE IF EXISTS {eval(f'{data_type}_DATA_TABLE')}")
               # cur.execute(f"CREATE TABLE IF NOT EXISTS {eval(f'{data_type}_DATA_TABLE')} ({', '.join(hdr_info)})")
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

   # @staticmethod
   # def _update_chunk(last_id):

   #    with sqlite3.connect(database_path) as worker_conn:
   #       worker_cur = worker_conn.cursor()
   #       update_query = f'''
   #          UPDATE {eval(f'{data_type}_DATA_TABLE')} 
   #          SET {SharedColumns.TIMESTAMPS} = ? 
   #          WHERE {SharedColumns.EVENT_ID} = ?
   #          '''
   #       chunk = pd.read_sql_query(f'''
   #          SELECT {SharedColumns.EVENT_ID},{SharedColumns.ISO_DATE} 
   #          FROM {eval(f'{data_type}_DATA_TABLE')} 
   #          WHERE {SharedColumns.EVENT_ID} >= {last_id} ORDER BY {SharedColumns.EVENT_ID}
   #          LIMIT {DATABASE_CHUNK_SIZE}
   #          ''', worker_conn)

   #       if chunk.empty:
   #          worker_cur.close()
   #          return True

   #       try:
   #          chunk[SharedColumns.TIMESTAMPS] = chunk[SharedColumns.ISO_DATE].apply(lambda x: parser.isoparse(x).timestamp())
   #       except ValueError as e:
   #          indices = chunk[chunk[SharedColumns.ISO_DATE].str.contains(":60\.", regex=True) == True].index
   #          chunk.loc[indices, SharedColumns.ISO_DATE] = chunk.loc[indices, SharedColumns.ISO_DATE].replace(":60\.", ":00.", regex=True)
   #          chunk[SharedColumns.TIMESTAMPS] = chunk[SharedColumns.ISO_DATE].apply(lambda x: parser.isoparse(x).timestamp())
   #       finally:
   #          worker_cur.executemany(update_query, chunk[[SharedColumns.TIMESTAMPS, SharedColumns.EVENT_ID]].values.tolist())
   #          worker_conn.commit()
   #       # cli_output.OK(f"{mp.current_process().name} UPDATED CHUNK FROM {last_id}")
   #       return False
   
   # @timer
   # def _update_timestamp_column(self, data_type):

   #    cur = self._db_conn.cursor()
   #    # cur.execute('PRAGMA journal_mode=WAL')
   #    last_id = 0
   #    update_query = f'''
   #       UPDATE {eval(f'{data_type}_DATA_TABLE')} 
   #       SET {SharedColumns.TIMESTAMPS} = ? 
   #       WHERE {SharedColumns.EVENT_ID} = ?
   #       '''

   #    # num_rows = cur.execute(f"SELECT COUNT(*) FROM {eval(f'{data_type}_DATA_TABLE')}").fetchone()[0]
   #    # output_name = self._mission_config["output_name"]
   #    # db_path = self._output_dir.joinpath(output_name, "database.db")
   #    # available_cores = mp.cpu_count()
   #    # update_pool = mp.Pool(
   #    #    processes=available_cores, 
   #    #    initializer=self._update_pool_init,
   #    #    initargs=(db_path, data_type)
   #    #    )

   #    while True:
   #       chunk = pd.read_sql_query(f'''
   #          SELECT {SharedColumns.EVENT_ID},{SharedColumns.ISO_DATE} 
   #          FROM {eval(f'{data_type}_DATA_TABLE')} 
   #          WHERE {SharedColumns.EVENT_ID} >= {last_id} ORDER BY {SharedColumns.EVENT_ID}
   #          LIMIT {DATABASE_CHUNK_SIZE}
   #          ''', self._db_conn)
   #       if chunk.empty:
   #          break
   #       try:
   #          chunk[SharedColumns.TIMESTAMPS] = chunk[SharedColumns.ISO_DATE].apply(lambda x: parser.isoparse(x).timestamp())
   #       except ValueError as e:
   #          indices = chunk[chunk[SharedColumns.ISO_DATE].str.contains(":60\.", regex=True)].index
   #          chunk.loc[indices, SharedColumns.ISO_DATE] = chunk.loc[indices, SharedColumns.ISO_DATE].replace(":60\.", ":00.", regex=True)
   #          chunk[SharedColumns.TIMESTAMPS] = chunk[SharedColumns.ISO_DATE].apply(lambda x: parser.isoparse(x).timestamp())
   #       finally:
   #          cur.executemany(update_query, chunk[[SharedColumns.TIMESTAMPS, SharedColumns.EVENT_ID]].values.tolist())
   #          last_id += DATABASE_CHUNK_SIZE

   #       # row_ids = [last_id + (i * DATABASE_CHUNK_SIZE) for i in range(available_cores)]
   #       # if last_id > num_rows:
   #       #    update_pool.close()
   #       #    update_pool.join()
   #       #    break
   #       # update_result = update_pool.map_async(
   #       #    func=self._update_chunk,
   #       #    # args=(last_id,),
   #       #    iterable=row_ids,
   #       #    # callback=self._update_complete,
   #       #    error_callback=self._update_error
   #       # )

   #       # chunk = pd.concat(update_result.get())
   #       # if chunk.empty:
   #       #    update_pool.close()
   #       #    update_pool.join()
   #       #    break
   #       # cur.executemany(update_query, chunk[[SharedColumns.TIMESTAMPS, SharedColumns.EVENT_ID]].values.tolist())

   #       # update_complete = any(update_result.get())
   #       # if update_complete:
   #       #    update_pool.close()
   #       #    update_pool.join()
   #       #    break

   #       # last_id += DATABASE_CHUNK_SIZE
   #       # last_id = row_ids[-1] + DATABASE_CHUNK_SIZE

   #    self._db_conn.commit()
   #    # cur.execute('PRAGMA journal_mode=DELETE')
   #    cur.close()

   def _check_database(self):

      cur = self._db_conn.cursor()
      try:
         comm_data_exists = cur.execute(f"SELECT EXISTS(SELECT 1 FROM {COMM_DATA_TABLE})").fetchone()[0]
         if not comm_data_exists:
            cli_output.FATAL("No comms data was collected during scenario execution... exiting!")
            shutil.rmtree(self._output_dir.joinpath(self._mission_config["output_name"]))
            sys.exit(1)
      except sqlite3.OperationalError as e:
         cli_output.FATAL("No comms table was created during scenario execution... exiting!")
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
   
   def _build_executor_file(self):

      with open(self._program_file.parent.joinpath("utils", "collector_files", "isr_afsim_collector.txt"), "r") as collector:
         collector_string = collector.read()

      output_name = self._mission_config["output_name"]
      executor_file = self._program_file.parent.joinpath(output_name + ".afsim")

      with open(executor_file, "w") as f:
         f.write("\n".join([self._get_include_docs(), collector_string, self._get_observer_block()]))

      return executor_file
   
   def _collect_data(self, executor_file, exec_endpoint):

      try:
         cli_output.INFO(f"Running mission for {self._startup_file}...")
         exec_endpoint.send("START MISSION")
         mission_result = subprocess.run(
            [self._mission_config["mission_exe_path"], str(executor_file.absolute())], 
            cwd=str(self._startup_file.parent), capture_output=True)

         if mission_result.returncode != 0:
            cli_output.FATAL("Mission execution error... exiting!")
            exec_endpoint.send("FAIL")
            ack = exec_endpoint.recv()
            exec_endpoint.close()
            os.remove(executor_file)
            sys.exit(1)

         cli_output.OK(f"Mission execution of {self._startup_file} successfully completed.")
         os.remove(executor_file)

      except NotADirectoryError as e:
         cli_output.FATAL(f"Mission execution error: {e.strerror}... exiting!")
         exec_endpoint.send("FAIL")
         ack = exec_endpoint.recv()
         exec_endpoint.close()
         os.remove(executor_file)
         sys.exit(1)

      except FileNotFoundError as e:
         cli_output.FATAL(f"Mission execution error: {e.strerror}... exiting!")
         exec_endpoint.send("FAIL")
         ack = exec_endpoint.recv()
         exec_endpoint.close()
         os.remove(executor_file)
         sys.exit(1)