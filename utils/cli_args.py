import argparse
import matplotlib.colors as colors
import utils.util_functions as utils


class CLIParser:

   def __init__(self):

      self._available_colors = list(colors.CSS4_COLORS.keys())
      self._parse_arguments()

   @property
   def arguments(self):
      return self._arguments

   @arguments.setter
   def arguments(self, value):
      raise AttributeError("Arguments are read-only")

   def _parse_arguments(self):

      cli_parser = argparse.ArgumentParser(
         prog="ISR-AFSIM Works",
         formatter_class=argparse.RawDescriptionHelpFormatter,
         description=
         '''
         This application helps to visualize and perform exploratory
         analysis of AFSIM ISR processes with the following features:
         1. Globe visualization of platforms with Plotly & CesiumJS
         2. Ability to filter communications data for a focused analysis.
         3. Bar Plots & 2D Network Plots
         ''')

      cli_parser.add_argument(
         "config_file",
         metavar="C:/path/to/file",
         type=str,
         help="JSON Config file to AFSIM execution and collection instructions."
      )

      cli_parser.add_argument(
         "-L", "--land-color",
         metavar="coral",
         dest="land_color",
         type=str,
         default=None,
         choices=self._available_colors,
         help="Land color on globe."
      )

      cli_parser.add_argument(
         "-O", "--ocean-color",
         metavar="aqua",
         dest="ocean_color",
         type=str,
         default=None,
         choices=self._available_colors,
         help="Ocean color on globe."
      )

      cli_parser.add_argument(
         "-R", "--resolution",
         metavar="low",
         dest="resolution",
         type=str,
         default="low",
         choices=["low", "medium", "high"],
         help="Globe surface resolution."
      )

      cli_parser.add_argument(
         "-C", "--classification",
         metavar="CUI",
         dest="classification",
         type=str,
         default=None,
         help="Classification of data used"
      )

      cli_parser.add_argument(
         "-Cs", "--cesium",
         dest="use_cesium",
         action="store_true",
         help="Flag to use CesiumJS as globe visualizer instead of Plotly."
      )

      cli_parser.add_argument(
         "--timer-enabled",
         dest="timer_enabled",
         action="store_true",
         help="Debug option to display timer results of important functions."
      )

      cli_parser.add_argument(
         "-v", "--verbose",
         action="count",
         default=0
      )

      cli_parser.add_argument("--version", action="version", version='%(prog)s 1.0.0')
      self._arguments = vars(cli_parser.parse_args())

      utils.TIMER_ENABLED = self._arguments.pop("timer_enabled")
      cli_output.VERBOSE = self._arguments.pop("verbose")


class cli_output:

   VERBOSE = 0

   def INFO(text):
      if cli_output.VERBOSE >= 2:
         print(f'\033[1;37m {text} \033[0;0m')

   def OK(text):
      print(f'\033[1;32m {text} \033[0;0m')

   def WARNING(text):
      if cli_output.VERBOSE >= 1:
         print(f'\033[1;33m {text} \033[0;0m')

   def FATAL(text):
      print(f'\033[1;31m {text} \033[0;0m')