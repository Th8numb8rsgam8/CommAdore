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
from ..dash_app import (
   CESIUM_CONFIG, 
   CESIUM_EXTERNAL, 
   CESIUM_INTERNAL, 
   CESIUM_TRACKS,
   CESIUM_VIEWER, 
   GLOBE_GRAPH, 
   CESIUM_CAMERA)

import pdb

class CesiumJSGlobe:

   def __init__(self, dash_app):

      self._offline_external_scripts = [
         {'src': get_asset_url("Cesium.js")},
         {'src': get_asset_url("Cesium_callbacks.jsm"), 'type': 'module'},
         {'src': get_asset_url("utils/comms_utils.jsm"), 'type': 'module'}]
      self._offline_external_stylesheets = ['/static/widgets.css']

      self._add_cesium_feature(dash_app)

   @staticmethod
   def get_line_points(sender_name, sender_location, receiver_name, receiver_location, platform_range):

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
         cli_output.WARNING(f"No line from {sender_name} to {receiver_name}.")
         return (
            [sender_location[0], receiver_location[0]],
            [sender_location[1], receiver_location[1]],
            [sender_location[2], receiver_location[2]])
      
      except TypeError as e:
         cli_output.WARNING(f"No line from {sender_name} to {receiver_name}.")
         return (
            [sender_location[0], receiver_location[0]],
            [sender_location[1], receiver_location[1]],
            [sender_location[2], receiver_location[2]])

   
   @classmethod
   def get_track_details(cls, track_data, platform_data):

      track_details = {}
      for platform, grp in track_data.groupby("Owning_Platform"):
         track_details[platform] = {}

         recent_track_info = grp.tail(1)
         receiver_location = recent_track_info[["PlatformLocation_X", "PlatformLocation_Y", "PlatformLocation_Z"]].iloc[0].to_numpy()
         master_track_list = recent_track_info["Master_Track_List"].iloc[0].strip().split(" ")
         current_time = datetime.utcfromtimestamp(recent_track_info["Timestamp"].iloc[0]).strftime("%H:%M:%S.%f")[:-3]
         track_details[platform]["CurrentTime"] = current_time
         track_details[platform]["Location"] = [receiver_location[0], receiver_location[1], receiver_location[2]]
         if recent_track_info["Event_Type"].iloc[0] == "LOCAL_TRACK_DROPPED":
            dropped_track = recent_track_info["Track_ID"].iloc[0]
            time_dropped = recent_track_info["ISODate"].iloc[0]
            master_track_list.remove(dropped_track)
            cli_output.INFO(f"{cls.__name__}: {dropped_track} dropped at {time_dropped}.")
         
         track_details[platform]["LocalTracks"] = {}
         for local_track in master_track_list:
            track_grp = grp[grp["Track_ID"] == local_track].tail(1)
            target_location = track_grp[["TargetLocation_X", "TargetLocation_Y", "TargetLocation_Z"]].iloc[0].to_numpy()
            platform_range = np.linalg.norm(receiver_location - target_location)
            x, y, z, = CesiumJSGlobe.get_line_points(
               platform, receiver_location,
               "target", target_location,
               platform_range)

            track_details[platform]["LocalTracks"][local_track] = {
               "TargetLocation": [target_location[0], target_location[1], target_location[2]],
               "TargetLine": {"x": x, "y": y, "z": z},
               "TimeSinceStarted": track_grp["Time_Since_Started"].iloc[0],
               "TimeSinceUpdated": track_grp["Time_Since_Updated"].iloc[0],
               "AltitudeKnown": bool(track_grp["Altitude_Known"].iloc[0]),
               "IsStale": bool(track_grp["Is_Stale"].iloc[0]),
               "Contributors": {}
            }
            raw_track_list = track_grp["Raw_Tracks"].iloc[0].strip().split(" ")
            for raw_track in raw_track_list:
               contributor_name = raw_track.split(".")[0]
               if contributor_name != "no_tracks":
                  try:
                     contributor_data = platform_data[platform_data["Platform_Name"] == contributor_name]
                     contributor_location = contributor_data[["Location_X", "Location_Y", "Location_Z"]].iloc[0].to_numpy()
                     platform_range = np.linalg.norm(receiver_location - contributor_location)
                     x, y, z, = CesiumJSGlobe.get_line_points(
                        contributor_name, contributor_location,
                        platform, receiver_location,
                        platform_range)

                     track_details[platform]["LocalTracks"][local_track]["Contributors"][contributor_name] = {
                        "Location": [contributor_location[0], contributor_location[1], contributor_location[2]],
                        "Line": {"x": x, "y": y, "z": z}
                     }
                  except IndexError as e:
                     cli_output.WARNING(f"{cls.__name__}: {contributor_name} does not exist at time {platform_data['ISODate'].iloc[0]}")

      return track_details

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
            function_name='track_contributions'
         ),
         Input(CESIUM_TRACKS, 'data'),
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