import subprocess
import sys, os, shutil
from pathlib import Path
from utils import cli_output
from dateutil import parser
import pandas as pd


class Executor:


   def __init__(self, mission_config):

      self._program_file = Path(sys.argv[0])
      self._mission_config = mission_config
      self._output_dir = self._program_file.parent.joinpath("output")

      self._required_events = [
         "enable SIMULATION_STARTING SetupParameters",
         "enable SIMULATION_COMPLETE FinishVisualization"]

      self._message_events = {
         "MESSAGE_OUTGOING": "enable MESSAGE_OUTGOING MessageOutgoing",
         "MESSAGE_INCOMING": "enable MESSAGE_INCOMING MessageIncoming",
         "MESSAGE_INTERNAL": "enable MESSAGE_INTERNAL MessageInternal",
         "MESSAGE_DELIVERY_ATTEMPT": "enable MESSAGE_DELIVERY_ATTEMPT MessageDeliveryAttempt",
         "MESSAGE_DISCARDED": "enable MESSAGE_DISCARDED MessageDiscarded",
         "MESSAGE_FAILED_ROUTING": "enable MESSAGE_FAILED_ROUTING MessageFailedRouting",
         "MESSAGE_HOP": "enable MESSAGE_HOP MessageHop",
         "MESSAGE_UPDATED": "enable MESSAGE_UPDATED MessageUpdated",
         "MESSAGE_QUEUED": "enable MESSAGE_QUEUED MessageQueued",
         "MESSAGE_RECEIVED": "enable MESSAGE_RECEIVED MessageReceived",
         "MESSAGE_TRANSMITTED": "enable MESSAGE_TRANSMITTED MessageTransmitted",
         "MESSAGE_TRANSMITTED_HEARTBEAT": "enable MESSAGE_TRANSMITTED_HEARTBEAT MessageTransmittedHeartbeat",
         "MESSAGE_TRANSMIT_ENDED": "enable MESSAGE_TRANSMIT_ENDED MessageTransmitEnded"
      }


   def get_afsim_data(self):

      if (self._mission_config["run_mission"]):
         self._execute_mission()
      
      return self._configure_data()

   def _execute_mission(self):

      observer_string = "\n   ".join(["observer", *self._required_events])
      for key, enabled in self._mission_config["message_events"].items():
         if enabled:
            observer_string = "\n   ".join([observer_string, self._message_events[key]])
         else:
            observer_string = "\n   ".join([observer_string, "# " + self._message_events[key]])
      observer_string += "\nend_observer"

      with open(self._program_file.parent.joinpath("utils", "comm_detail_collector.txt"), "r") as collector:
         collector_string = collector.read()
         
      output_name = self._mission_config["output_name"]
      comms_file = self._program_file.parent.joinpath(output_name + ".afsim")
      startup_file = Path(self._mission_config["scenario_startup"])
      include_doc = "include_once " + str(startup_file.absolute().as_posix()) 
      with open(comms_file, "w") as f:
         f.write("\n".join([include_doc, collector_string, observer_string]))

      cli_output.INFO(f"Running mission for {startup_file}...")
      mission_result = subprocess.run(
         [self._mission_config["mission_exe_path"], str(comms_file.absolute())], 
         cwd=str(startup_file.parent))

      if mission_result.returncode != 0:
         cli_output.FATAL("Mission execution error... exiting!")
         os.remove(comms_file)
         sys.exit(1)

      cli_output.OK(f"Mission execution of {startup_file} successfully completed.")
      os.remove(comms_file)

      if not self._output_dir.exists():
         os.mkdir(self._output_dir)
      shutil.move(
         startup_file.parent.joinpath("comms_analysis.csv"),
         self._output_dir.joinpath(output_name + ".csv"))


   def _configure_data(self, ran_mission=True):

      substitutions = {
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
         'Sender_Type': 'unknown',
         'Sender_BaseType': 'unknown',
         'SenderPart_Type': 'unknown',
         'SenderPart_BaseType': 'unknown',
         'Receiver_Name': 'Does Not Exist',
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

      output_name = self._mission_config["output_name"]
      csv_file_path = self._output_dir.joinpath(output_name + ".csv")

      if not csv_file_path.exists():
         cli_output.FATAL(f"{csv_file_path.absolute()} does not exist... exiting!")
         sys.exit(1)

      df = pd.read_csv(csv_file_path).fillna(value=substitutions)
      df["Timestamp"] = df["ISODate"].apply(lambda x: parser.isoparse(x).timestamp())

      return df