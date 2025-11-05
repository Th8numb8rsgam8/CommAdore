import sys
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from flask import make_response
from dash import Input, Output, State, ClientsideFunction
from .globe_methods import GlobeMethods
from utils import cli_output
from ..dash_app import (
   CESIUM_CONFIG, 
   CESIUM_EXTERNAL, 
   CESIUM_INTERNAL, 
   CESIUM_VIEWER, 
   GLOBE_GRAPH, 
   CESIUM_CAMERA)


class CesiumJSGlobe:

   def __init__(self, dash_app):

      self._offline_external_scripts = [{'src': '/assets/Cesium.js'}]
      self._offline_external_stylesheets = ['/static/widgets.css']

      self._add_cesium_feature(dash_app)

   @staticmethod
   def get_line_points(group):
      sender_location = np.array([
         group["SenderLocation_X"].values[0], 
         group["SenderLocation_Y"].values[0], 
         group["SenderLocation_Z"].values[0]])

      receiver_location = np.array([
         group["ReceiverLocation_X"].values[0], 
         group["ReceiverLocation_Y"].values[0], 
         group["ReceiverLocation_Z"].values[0]])
                  
      platform_range = group["SenderToRcvr_Range"].values[0]

      if 0 < platform_range <= 1000:
         interval = 50
      elif 1000 < platform_range <= 10000:
         interval = 500
      elif 10000 < platform_range <= 50000:
         interval = 2500
      elif 50000 < platform_range <= 100000:
         interval = 5000
      elif 100000 < platform_range <= 500000:
         interval = 25000
      elif 500000 < platform_range <= 1000000:
         interval = 50000
      elif 1000000 < platform_range <= 5000000:
         interval = 250000
      elif 5000000 < platform_range <= 10000000:
         interval = 500000
      elif 10000000 < platform_range <= 50000000:
         interval = 2500000
      elif 50000000 < platform_range:
         interval = 5000000

      try:
         num_arrows, remainder = divmod(platform_range, interval)
         delta = (0.5 * remainder / platform_range) * (receiver_location - sender_location)
         first_arrow = sender_location + delta
         last_arrow = receiver_location - delta

         if GlobeMethods.los_hits_horizon(sender_location, receiver_location):
            return GlobeMethods.get_curve_points_on_sphere(first_arrow, last_arrow, int(num_arrows) if num_arrows != 0 else 10)
         else:
            return GlobeMethods.get_points_on_line_segment(first_arrow, last_arrow, int(num_arrows) if num_arrows != 0 else 10)

      except UnboundLocalError as e:
         cli_output.WARNING(f"No transmission line from {group['Sender_Name'].iloc[0]} to {group['Receiver_Name'].iloc[0]}.")
         return (
            [sender_location[0], receiver_location[0]],
            [sender_location[1], receiver_location[1]],
            [sender_location[2], receiver_location[2]])

   @staticmethod
   def set_camera_view(internal_df, external_df):

      camera_zoom = GlobeMethods.EQUATOR_RADIUS * 3 
      internal_pts = internal_df[["SenderLocation_X", "SenderLocation_Y", "SenderLocation_Z"]]
      sender_pts = external_df[["SenderLocation_X", "SenderLocation_Y", "SenderLocation_Z"]]
      rcvr_pts = external_df[["ReceiverLocation_X", "ReceiverLocation_Y", "ReceiverLocation_Z"]]
      rcvr_pts = rcvr_pts.rename(columns=
         {"ReceiverLocation_X": "SenderLocation_X",
          "ReceiverLocation_Y": "SenderLocation_Y",
          "ReceiverLocation_Z": "SenderLocation_Z"})

      points_df = pd.concat([internal_pts, sender_pts, rcvr_pts], ignore_index=True)

      with warnings.catch_warnings():
         warnings.filterwarnings('error', category=RuntimeWarning)
         try:
            camera_location = points_df.dropna(axis=0).drop_duplicates().values.mean(axis=0)
            camera_vector = camera_location / np.linalg.norm(camera_location)
            camera_zoom = 2 * points_df.apply(lambda x: np.linalg.norm(x), axis=1).max()
            camera_center = camera_zoom * camera_vector
            return {"x": camera_center[0], "y": camera_center[1], "z": camera_center[2]}
         except RuntimeWarning as e:
            return {"x": camera_zoom, "y": 0, "z": 0}
 

   def _add_cesium_feature(self, app):

      app.config.external_scripts.extend(self._offline_external_scripts)

      app.config.external_stylesheets.extend(self._offline_external_stylesheets)

      app.clientside_callback(
         ClientsideFunction(
            namespace='Cesium',
            function_name='startup_cesium'
         ),
         Output(CESIUM_VIEWER, 'data'),
         Input(GLOBE_GRAPH, 'id'),
         State(CESIUM_CONFIG, 'data')
      )

      app.clientside_callback(
         ClientsideFunction(
            namespace='Cesium',
            function_name='external_transmissions'
         ),
         Input(CESIUM_EXTERNAL, 'data'),
         Input(CESIUM_VIEWER, 'data')
      )

      app.clientside_callback(
         ClientsideFunction(
            namespace='Cesium',
            function_name='internal_transmissions'
         ),
         Input(CESIUM_INTERNAL, 'data'),
         Input(CESIUM_VIEWER, 'data')
      )

      app.clientside_callback(
         ClientsideFunction(
            namespace='Cesium',
            function_name='camera_view'
         ),
         Input(CESIUM_CAMERA, 'data'),
         Input(CESIUM_VIEWER, 'data')
      )

      @app.server.route("/world")
      def get_world_image():

         startup_file = Path(sys.argv[0])
         world_file = startup_file.parent.joinpath("earth_data", "world.jpg")

         with open(world_file, 'rb') as f:
            response = make_response(f.read())
            response.headers["Content-Type"] = 'text/plain'
            response.headers["Access-Control-Allow-Origin"] = '*'
            return response