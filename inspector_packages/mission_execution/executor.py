import csv
import subprocess
import sqlite3
import sys, os, shutil
import multiprocessing as mp
from pathlib import Path
from utils import cli_output, timer
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
         "COMM": "comms_analysis.csv",
         "TRACK": "track_analysis.csv",
         "PLATFORM": "platform_status.csv"
      }

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

      self._track_events = {
         "LOCAL_TRACK_CORRELATION": "enable LOCAL_TRACK_CORRELATION track_LocalTrackCorrelation",
         "LOCAL_TRACK_DECORRELATION": "enable LOCAL_TRACK_CORRELATION track_LocalTrackCorrelation",
         "LOCAL_TRACK_INITIATED": "enable LOCAL_TRACK_INITIATED track_LocalTrackInitiated",
         "LOCAL_TRACK_UPDATED": "enable LOCAL_TRACK_UPDATED track_LocalTrackUpdated",
         "LOCAL_TRACK_DROPPED": "enable LOCAL_TRACK_DROPPED track_LocalTrackDropped"
      }

   @property
   def database(self):
      return self._db_conn

   @property
   def queue_info(self):
      return self._queue_info

   def get_afsim_data(self):

      if (self._mission_config["run_mission"]):
         self._execute_mission()
         self._store_data()

      self._retrieve_data()

   def _execute_mission(self):

      executor_file = self._build_executor_file()
      self._collect_data(executor_file)

   def _store_data(self):

      output_name = self._mission_config["output_name"]
      self._db_conn = sqlite3.connect(self._output_dir.joinpath(output_name, "database.db"))

      self._store_in_database("COMM")
      self._store_in_database("TRACK")
      self._store_in_database("PLATFORM")
      self._check_database()
      self._empty_value_substitutions("COMM")
      self._empty_value_substitutions("TRACK")
      self._db_conn.close()

      # comm_df["Timestamp"] = comm_df["ISODate"].apply(lambda x: parser.isoparse(x).timestamp())
      # if not comm_df.empty:
      #    comm_df["Timestamp"] = comm_df["Timestamp"].round(decimals=1)
      #    comm_df["SimulationTime"] = comm_df["SimulationTime"].round(decimals=2)

      # track_df["Timestamp"] = track_df[ISO_DATE].apply(lambda x: parser.isoparse(x).timestamp())
      # if not track_df.empty:
      #    track_df["Timestamp"] = track_df["Timestamp"].round(decimals=1)
      #    track_df[SIMULATION_TIME] = track_df[SIMULATION_TIME].round(decimals=2)

      # platform_df["Timestamp"] = platform_df[ISO_DATE].apply(lambda x: parser.isoparse(x).timestamp())
      # if not platform_df.empty:
      #    platform_df["Timestamp"] = platform_df["Timestamp"].round(decimals=2)
      #    platform_df[SIMULATION_TIME] = platform_df[SIMULATION_TIME].round(decimals=2)


   def _retrieve_data(self):

      try:
         output_name = self._mission_config["output_name"]
         db_dir = self._output_dir.joinpath(output_name, "database.db")
         self._db_conn = sqlite3.connect(db_dir, check_same_thread=False)
      except sqlite3.OperationalError as e:
         cli_output.FATAL(f'{str(e).upper()}: {db_dir}')
         if self._output_dir.exists():
            datasets = [f'{idx+1} {result.name}' for idx, result in enumerate(self._output_dir.iterdir())]
            data_list = "\n".join(datasets)
            cli_output.FATAL(f"The following datasets are available: \n{data_list}")
         sys.exit(1)

   @timer
   def _store_in_database(self, data_type):

      cur = self._db_conn.cursor()
      file_path = self._startup_file.parent.joinpath(self._file_names[data_type])
      with open(file_path, 'r', newline='', encoding='utf-8') as f:
         reader = csv.reader(f)
         headers = next(reader)

         hdr_info = []
         for hdr in headers:
            col = f"{hdr} {eval(f'SQLITE_{data_type}_DATA_TYPES')[hdr]}"
            hdr_info.append(col)

         cur.execute(f"DROP TABLE IF EXISTS {eval(f'{data_type}_DATA_TABLE')}")
         cur.execute(f"CREATE TABLE IF NOT EXISTS {eval(f'{data_type}_DATA_TABLE')} ({', '.join(hdr_info)})")

         placeholders = ["?"] * len(headers)
         insertion_cmd = f"INSERT INTO {eval(f'{data_type}_DATA_TABLE')} VALUES ({','.join(placeholders)})"
         cur.executemany(insertion_cmd, reader)
      
      self._db_conn.commit()
      cur.close()
      os.remove(file_path)

   @staticmethod
   def _update_pool_init(db_path, dtype):
      global data_type
      global database_path
      data_type = dtype
      database_path = db_path
      # cli_output.OK(f'{mp.current_process().name} INITIALIZED')

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
   
   @staticmethod
   def _update_error(exc):

      cli_output.FATAL(f"UPDATE ERROR: {exc}")

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

   @timer
   def _empty_value_substitutions(self, data_type):

      cur = self._db_conn.cursor()
      last_id = 0
      update_query = f'''
         UPDATE {eval(f'{data_type}_DATA_TABLE')} 
         SET {' = ?, '.join(eval(f'{data_type}_SUBSTITUTIONS'))} = ?
         WHERE {SharedColumns.EVENT_ID} = ?
         '''
      while True:
         chunk = pd\
            .read_sql_query(f'''
               SELECT {",".join(eval(f'{data_type}_SUBSTITUTIONS'))},{SharedColumns.EVENT_ID}
               FROM {eval(f'{data_type}_DATA_TABLE')}
               WHERE {SharedColumns.EVENT_ID} >= {last_id} ORDER BY {SharedColumns.EVENT_ID}
               LIMIT {DATABASE_CHUNK_SIZE}
               ''', self._db_conn)\
            .replace(r'^\s*$', np.nan, regex=True)\
            .fillna(value=eval(f'{data_type}_SUBSTITUTIONS'))
         if chunk.empty:
            break
         last_id += DATABASE_CHUNK_SIZE
         cur.executemany(update_query, chunk.values.tolist())

      self._db_conn.commit()
      cur.close()

   def _check_database(self):

      cur = self._db_conn.cursor()
      comm_data_exists = cur.execute(f"SELECT EXISTS(SELECT 1 FROM {COMM_DATA_TABLE})").fetchone()[0]
      if not comm_data_exists:
         cli_output.FATAL("No comms data was collected during scenario execution... exiting!")
         shutil.rmtree(self._output_dir.joinpath(self._mission_config["output_name"]))
         sys.exit(1)

      track_data_exists = cur.execute(f"SELECT EXISTS(SELECT 1 FROM {TRACK_DATA_TABLE})").fetchone()[0]
      if not track_data_exists:
         cli_output.WARNING("No track data was collected during scenario execution!")

      platform_data_exists = cur.execute(f"SELECT EXISTS(SELECT 1 FROM {PLATFORM_DATA_TABLE})").fetchone()[0]
      if not platform_data_exists:
         cli_output.WARNING("No platform data was collected during scenario execution!")

      cur.close()


   def _get_observer_block(self):

      observer_block = "\n   ".join(["observer", *self._required_events])
      for key, enabled in self._mission_config["message_events"].items():
         if enabled:
            observer_block = "\n   ".join([observer_block, self._message_events[key]])
         else:
            observer_block = "\n   ".join([observer_block, "# " + self._message_events[key]])

      for key, event in self._track_events.items():
         observer_block = "\n   ".join([observer_block, event])
      observer_block += "\nend_observer"
   
      return observer_block
   
   def _get_include_docs(self):

      include_doc = "include_once " + str(self._startup_file.absolute().as_posix()) + "\n"

      include_doc += "include_once " + self._program_file.parent.absolute().joinpath(
         "utils", "collector_files", "comm_detail_collector.txt").as_posix() + "\n"

      include_doc += "include_once " + self._program_file.parent.absolute().joinpath(
         "utils", "collector_files", "track_detail_collector.txt").as_posix() + "\n"

      include_doc += "include_once " + self._program_file.parent.absolute().joinpath(
         "utils", "collector_files", "platform_status_collector.txt").as_posix() + "\n"

      return include_doc
   
   def _build_executor_file(self):

      with open(self._program_file.parent.joinpath("utils", "collector_files", "isr_afsim_collector.txt"), "r") as collector:
         collector_string = collector.read()

      output_name = self._mission_config["output_name"]
      executor_file = self._program_file.parent.joinpath(output_name + ".afsim")

      with open(executor_file, "w") as f:
         f.write("\n".join([self._get_include_docs(), collector_string, self._get_observer_block()]))

      return executor_file
   
   def _collect_data(self, executor_file):

      try:
         cli_output.INFO(f"Running mission for {self._startup_file}...")
         mission_result = subprocess.run(
            [self._mission_config["mission_exe_path"], str(executor_file.absolute())], 
            cwd=str(self._startup_file.parent))

         if mission_result.returncode != 0:
            cli_output.FATAL("Mission execution error... exiting!")
            os.remove(executor_file)
            sys.exit(1)

         self._check_output_file_exists("COMM", executor_file)
         self._check_output_file_exists("TRACK", executor_file)
         self._check_output_file_exists("PLATFORM", executor_file)

         cli_output.OK(f"Mission execution of {self._startup_file} successfully completed.")
         os.remove(executor_file)

         if not self._output_dir.exists():
            os.mkdir(self._output_dir)

         output_name = self._mission_config["output_name"]
         if not self._output_dir.joinpath(output_name).exists():
            os.mkdir(self._output_dir.joinpath(output_name))

      except NotADirectoryError as e:
         cli_output.FATAL(f"Mission execution error: {e.strerror}... exiting!")
         os.remove(executor_file)
         sys.exit(1)

      except FileNotFoundError as e:
         cli_output.FATAL(f"Mission execution error: {e.strerror}... exiting!")
         os.remove(executor_file)
         sys.exit(1)

      except KeyboardInterrupt as e:
         os.remove(executor_file)
         raise KeyboardInterrupt

   def _check_output_file_exists(self, file_name, executor_file):

      file_path = self._startup_file.parent.joinpath(self._file_names[file_name])
      if not file_path.exists():
         cli_output.FATAL(f"{file_path.absolute()} does not exist... exiting!")
         if self._output_dir.exists():
            datasets = [f'{idx+1} {result.name}' for idx, result in enumerate(self._output_dir.iterdir())]
            data_list = "\n".join(datasets)
            cli_output.FATAL(f"The following datasets are available: \n{data_list}")
         os.remove(executor_file)
         sys.exit(1)