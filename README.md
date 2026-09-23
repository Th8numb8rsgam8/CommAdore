# CommADore
The purpose of  this application is to perform exploratory analysis
of AFSIM ISR elements and processes, particularly information flow. It executes and collects event data from an AFSIM scenario and displays it on a globe and also includes bar plots and 2D network plots. The current version focuses on capturing and analyzing comms events, but future versions are expected to also include sensor detections and track formations.

## Setup Requirements
1. Install Python (tested with 3.11)
2. Create/Enter Python environment
   1. Virtual environment option
      ```
      python -m venv <environment-name>
      .\<environment-name>\Scripts\Activate.ps1
      ```
   2. Anaconda environment option
      ```
      conda create --name <environment-name> python=<python-version>
      conda activate <environment-name>
      ```
3. Install required packages `pip install -r requirements.txt`

## Running Script
* This application requires a config file in JSON format as argument
* Refer to **config_file.json** for config details
* To avoid running **mission** every time a script is executed, set **run_mission** to **false**
* The script collects events and generates a CSV file in **output** folder which is used as a data source for the visualizations & analysis
* Please note that the following events are not a part of default **mission** and should be set to false prior to execution
  * MESSAGE_OUTGOING
  * MESSAGE_INCOMING
  * MESSAGE_INTERNAL
```
positional arguments:
  C:/path/to/file.json    JSON Config file 

optional arguments:
  -h, --help              show this help message and exit
  -L, --land-color        land color on Plotly globe 
  -O, --ocean-color       ocean color on Plotly globe
  -R, --resolution        Plotly globe surface resolution
  -C, --classification    classification banner markings
  -Cs, --cesium           Flag to use CesiumJS as globe instead of Plotly
  --timer-enabled         Debug option to display timer results of important functions
  --mission-output        Option to display mission execution output
  -v, --verbose           Display application info at various levels
  --version               show program's version
```

## CesiumJS ![](/assets/Assets/Images/cesium_credit.png)
Cesium is an open-source software that helps to visualize geospatial data, and CommAdore leverages this useful tool to view **mission** data on a globe.
Cesium is integrated with Python Dash to visualize both the globe and Plotly figures. By default, this application requests Bing Maps to display the globe, which requires an access token. Refer to [Cesium Access Tokens](https://www.cesium.com/learn/ion/cesium-ion-access-tokens/) for instructions on how to obtain your own access token and to include it in the config file. If an access token is invalid or is not provided, Cesium requests for a local resource located in **/earth_data/world.jpg**. The world image is wrapped around a surface
for a 3D appearance.