import sys
from utils import *


if __name__ == "__main__":

   try:
      cli_parser = CLIParser()
      visualizer = Inspector(**cli_parser.arguments)
      visualizer.run()
   except KeyboardInterrupt as e:
      cli_output.FATAL("Program aborted!")
      sys.exit(1)