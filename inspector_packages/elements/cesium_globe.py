import sys
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from flask import make_response, request
from dash import Input, Output, State, ClientsideFunction, get_asset_url
from .globe_methods import GlobeMethods
from utils import cli_output
from ..mission_execution import *
from ..dash_app import (
   CESIUM_CONFIG, 
   CESIUM_EXTERNAL, 
   CESIUM_INTERNAL, 
   CESIUM_VIEWER, 
   GLOBE_GRAPH, 
   CESIUM_CAMERA)


class CesiumJSGlobe:

   def __init__(self, dash_app):

      self._offline_external_scripts = [
         {'src': get_asset_url("Cesium.js")},
         {'src': get_asset_url("Cesium_callbacks.jsm"), 'type': 'module'},
         {'src': get_asset_url("utils/comms_utils.jsm"), 'type': 'module'}]
      self._offline_external_stylesheets = ['/static/widgets.css']

      self._add_cesium_feature(dash_app)

   @classmethod
   def get_line_points(cls, sender_name, sender_location, receiver_name, receiver_location, platform_range):

      interval = CesiumJSGlobe._get_arrow_interval(platform_range)

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
         cli_output.WARNING(f"{cls.__name__}: No line from {sender_name} to {receiver_name}.")
         return (
            [sender_location[0], receiver_location[0]],
            [sender_location[1], receiver_location[1]],
            [sender_location[2], receiver_location[2]])
      
      except TypeError as e:
         cli_output.WARNING(f"{cls.__name__}: No line from {sender_name} to {receiver_name}.")
         return (
            [sender_location[0], receiver_location[0]],
            [sender_location[1], receiver_location[1]],
            [sender_location[2], receiver_location[2]])

   
   @staticmethod
   def set_camera_view(internal_df, external_df):

      camera_zoom = GlobeMethods.EQUATOR_RADIUS * 3 
      internal_pts = internal_df[
         [CommDataColumns.SENDERLOCATION_X, 
          CommDataColumns.SENDERLOCATION_Y, 
          CommDataColumns.SENDERLOCATION_Z]]
      sender_pts = external_df[
         [CommDataColumns.SENDERLOCATION_X, 
          CommDataColumns.SENDERLOCATION_Y, 
          CommDataColumns.SENDERLOCATION_Z]]
      rcvr_pts = external_df[
         [CommDataColumns.RECEIVERLOCATION_X, 
          CommDataColumns.RECEIVERLOCATION_Y, 
          CommDataColumns.RECEIVERLOCATION_Z]]
      rcvr_pts = rcvr_pts.rename(columns=
         {CommDataColumns.RECEIVERLOCATION_X: CommDataColumns.SENDERLOCATION_X,
          CommDataColumns.RECEIVERLOCATION_Y: CommDataColumns.SENDERLOCATION_Y,
          CommDataColumns.RECEIVERLOCATION_Z: CommDataColumns.SENDERLOCATION_Z})

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
 
   @staticmethod
   def _get_arrow_interval(platform_range):

      if 0 < platform_range <= 1000:
         return 50
      elif 1000 < platform_range <= 10000:
         return 500
      elif 10000 < platform_range <= 50000:
         return 2500
      elif 50000 < platform_range <= 100000:
         return 5000
      elif 100000 < platform_range <= 500000:
         return 25000
      elif 500000 < platform_range <= 1000000:
         return 50000
      elif 1000000 < platform_range <= 5000000:
         return 250000
      elif 5000000 < platform_range <= 10000000:
         return 500000
      elif 10000000 < platform_range <= 50000000:
         return 2500000
      elif 50000000 < platform_range:
         return 5000000

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

      @app.server.route(get_asset_url("utils/comms_utils.jsm"))
      @app.server.route(get_asset_url("Cesium_callbacks.jsm"))
      def get_cesium_assets():

         startup_file = Path(sys.argv[0])
         _, assets, *name = request.path.split("/")
         asset_file = startup_file.parent.joinpath(assets, *name)

         with open(asset_file, 'rb') as f:
            response = make_response(f.read())
            response.headers["Content-Type"] = 'application/javascript'
         return response