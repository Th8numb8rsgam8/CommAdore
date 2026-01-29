import json, sys
import webbrowser
from .cli_args import cli_output
from inspector_packages.dash_app.dash_callbacks import DashCallbacks
from inspector_packages.mission_execution.executor import Executor
from pathlib import Path


class Inspector:

   def __init__(self, 
      config_file=None, 
      land_color=None, 
      ocean_color=None, 
      resolution=None,
      classification=None,
      use_cesium=False):

      self._host = "127.0.0.1"
      self._port = 8050

      mission_config, cesium_config = self._extract_configs(config_file)

      self._mission_executor = Executor(mission_config)
      self._mission_executor.get_afsim_data()

      self._callbacks = DashCallbacks(
         self._mission_executor.database,
         land_color, ocean_color, 
         resolution, classification, 
         json.dumps(cesium_config),
         use_cesium)

   def run(self):
      webbrowser.open(f"http://{self._host}:{self._port}/")
      self._callbacks.app.run(debug=False, host=self._host, port=self._port)

   def _extract_configs(self, config_file):

      config_file = Path(config_file)

      if not config_file.exists():
         cli_output.FATAL(f'{config_file.absolute()} file does not exist.')
         sys.exit(1)

      if not config_file.is_file():
         cli_output.FATAL(f'{config_file.absolute()} is not a file.')
         sys.exit(1)

      with open(config_file, 'r') as f:
         config = json.load(f)
         try:
            mission_config = config["mission"]
         except KeyError as e:
            cli_output.FATAL("Mission config does not exist... exiting!")
            sys.exit(1)

         try:
            cesium_config = config["cesium"]
            cesium_config["local_server"] = f"http://{self._host}:{self._port}/"
         except KeyError as e:
            cli_output.WARNING("Cesium config does not exist... adding default options.")
            cesium_config = {
               "cesium_token": "defaultAccessToken",
               "local_server": f"http://{self._host}:{self._port}/"
               }

         return mission_config, cesium_config