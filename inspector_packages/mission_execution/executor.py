import copy
import subprocess
import sys, os, shutil
from pathlib import Path
from utils import cli_output
from dateutil import parser
import pandas as pd

import pdb

class Executor:

   COMM_SUBSTITUTIONS = {
      'Message_SerialNumber': -1,
      'Message_Originator': 'unknown',
      'Message_Size': -1,
      'Message_Priority': -1,
      'Message_DataTag': -1,
      'OldMessage_SerialNumber': -1,
      'OldMessage_Originator': 'unknown',
      'OldMessage_Type': 'Does Not Exist',
      'OldMessage_Size': -1,
      'OldMessage_Priority': -1,
      'OldMessage_DataTag': -1,
      'Sender_Side': 'unknown',
      'Sender_Type': 'unknown',
      'Sender_BaseType': 'unknown',
      'SenderPart_Type': 'unknown',
      'SenderPart_BaseType': 'unknown',
      'Receiver_Name': 'Does Not Exist',
      'Receiver_Side': 'unknown',
      'Receiver_Type': 'unknown',
      'Receiver_BaseType': 'unknown',
      'ReceiverPart_Name': 'Does Not Exist',
      'ReceiverPart_Type': 'unknown',
      'ReceiverPart_BaseType': 'unknown',
      'CommInteraction_Succeeded': -1,
      'CommInteraction_Failed': -1,
      'CommInteraction_FailedStatus': 'Does Not Exist',
      'Queue_Size': -1
   }

   TRACK_SUBSTITUTIONS = {
      "NonLocal_Track_ID": "no_track",
      "Raw_Tracks": "no_tracks"
   }


   def __init__(self, mission_config):

      self._program_file = Path(sys.argv[0])
      self._mission_config = mission_config
      self._startup_file = Path(self._mission_config["scenario_startup"])
      self._output_dir = self._program_file.parent.joinpath("output")

      self._comms_file_name = "comms_analysis.csv"
      self._platform_file_name = "platform_status.csv"
      self._track_file_name = "track_analysis.csv"

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


   def get_afsim_data(self):

      if (self._mission_config["run_mission"]):
         self._execute_mission()
      
      return self._configure_data()

   def _execute_mission(self):

      executor_file = self._build_executor_file()

      self._collect_data(executor_file)


   def _configure_data(self):

      self._check_output_file_exists(self._comms_file_name)
      self._check_output_file_exists(self._track_file_name)
      self._check_output_file_exists(self._platform_file_name)

      file_path = self._output_dir.joinpath(self._mission_config["output_name"],  self._comms_file_name)
      comm_df = pd.read_csv(file_path).fillna(value=Executor.COMM_SUBSTITUTIONS)
      if comm_df.empty:
         cli_output.FATAL("No comms data was collected during scenario execution... exiting!")
         sys.exit(1)

      file_path = self._output_dir.joinpath(self._mission_config["output_name"],  self._track_file_name)
      track_df = pd.read_csv(file_path).fillna(value=Executor.TRACK_SUBSTITUTIONS)
      if track_df.empty:
         cli_output.WARNING("No track data was collected during scenario execution!")

      file_path = self._output_dir.joinpath(self._mission_config["output_name"],  self._platform_file_name)
      platform_df = pd.read_csv(file_path)
      if platform_df.empty:
         cli_output.WARNING("No platform data was collected during scenario execution!")
      
      comm_df["Timestamp"] = comm_df["ISODate"].apply(lambda x: parser.isoparse(x).timestamp())
      track_df["Timestamp"] = track_df["ISODate"].apply(lambda x: parser.isoparse(x).timestamp())
      platform_df["Timestamp"] = platform_df["ISODate"].apply(lambda x: parser.isoparse(x).timestamp())

      queue_info = self._get_queue_info(comm_df)

      return {
         "comm": comm_df, 
         "track": track_df, 
         "platform": platform_df, 
         "queues": queue_info
      }

   def _get_queue_info(self, df):

      queue_events = df[df["Event_Type"].isin(["MESSAGE_QUEUED", "MESSAGE_TRANSMITTED"])]
      queue_info = {sender: {} for sender in queue_events["Sender_Name"].unique()}
      for sender, group in queue_events.groupby("Sender_Name"):
         queue_info[sender] = {t: {} for t in group["Timestamp"].unique()}
         comms = group["SenderPart_Name"].unique()
         comms_update = {comm: [] for comm in comms}
         for timestamp, time_grp in group.groupby("Timestamp"):
            queue_info[sender][timestamp] = {comm: [] for comm in comms}
            for _, row in time_grp.iterrows():
               sender_comm = row["SenderPart_Name"]
               if row["Event_Type"] == "MESSAGE_QUEUED":
                  comms_update[sender_comm].append((row["Message_SerialNumber"], row["Message_Type"]))
               elif row["Event_Type"] == "MESSAGE_TRANSMITTED":
                  comms_update[sender_comm].remove((row["Message_SerialNumber"], row["Message_Type"]))
               
               increased_queue = len(comms_update[sender_comm]) > len(queue_info[sender][timestamp][sender_comm])
               if increased_queue:
                  queue_info[sender][timestamp][sender_comm] = copy.deepcopy(comms_update[sender_comm])

      return queue_info

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

         cli_output.OK(f"Mission execution of {self._startup_file} successfully completed.")
         os.remove(executor_file)

         if not self._output_dir.exists():
            os.mkdir(self._output_dir)
         
         output_name = self._mission_config["output_name"]
         if not self._output_dir.joinpath(output_name).exists():
            os.mkdir(self._output_dir.joinpath(output_name))

         shutil.move(
            self._startup_file.parent.joinpath(self._comms_file_name),
            self._output_dir.joinpath(output_name, self._comms_file_name))
         shutil.move(
            self._startup_file.parent.joinpath(self._platform_file_name),
            self._output_dir.joinpath(output_name, self._platform_file_name))
         shutil.move(
            self._startup_file.parent.joinpath(self._track_file_name),
            self._output_dir.joinpath(output_name, self._track_file_name))
         
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

   def _check_output_file_exists(self, file_name):

      file_path = self._output_dir.joinpath(self._mission_config["output_name"],  file_name)

      if not file_path.exists():
         cli_output.FATAL(f"{file_path.absolute()} does not exist... exiting!")
         if self._output_dir.exists():
            datasets = [f'{idx+1} {result.name}' for idx, result in enumerate(self._output_dir.iterdir())]
            data_list = "\n".join(datasets)
            cli_output.FATAL(f"The following datasets are available: \n{data_list}")
         sys.exit(1)