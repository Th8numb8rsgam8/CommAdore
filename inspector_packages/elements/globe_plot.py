import pickle, warnings
from pathlib import Path
import pandas as pd
from inspector_packages import *
from .globe_methods import GlobeMethods

import pdb

class GlobePlot:

   CAMERA_ZOOM = 3

   def __init__(self, data, land_color, ocean_color, resolution):

      self._camera_view = {"x": GlobePlot.CAMERA_ZOOM, "y": 0, "z": 0}

      self._current_file = Path(__file__) 

      self._set_earth_surface(land_color, ocean_color, resolution)
      self._set_axes_attributes(data)


   def build_earth_figure(self, traces):

      fig = go.Figure(
         {
            "data": [self._earth_surface] + traces,
            "layout": self._globe_layout()
         }
      )

      return fig


   def set_camera_view(self, data):

      internal_df = data["comm"]["internal"]
      external_df = data["comm"]["external"]
      track_df = data["track"]
      platform_df = data["platform"]

      internal_pts = internal_df[["SenderLocation_X", "SenderLocation_Y", "SenderLocation_Z"]]
      sender_pts = external_df[["SenderLocation_X", "SenderLocation_Y", "SenderLocation_Z"]]
      rcvr_pts = external_df[["ReceiverLocation_X", "ReceiverLocation_Y", "ReceiverLocation_Z"]]
      rcvr_pts = rcvr_pts.rename(columns=
         {"ReceiverLocation_X": "SenderLocation_X",
          "ReceiverLocation_Y": "SenderLocation_Y",
          "ReceiverLocation_Z": "SenderLocation_Z"})

      platform_pts = platform_df[["Location_X", "Location_Y", "Location_Z"]]
      platform_pts = platform_pts.rename(columns=
         {"Location_X": "SenderLocation_X",
          "Location_Y": "SenderLocation_Y",
          "Location_Z": "SenderLocation_Z"})

      points_df = pd.concat([internal_pts, sender_pts, rcvr_pts, platform_pts], ignore_index=True)

      with warnings.catch_warnings():
         warnings.filterwarnings('error', category=RuntimeWarning)
         try:
            camera_location = points_df.dropna(axis=0).drop_duplicates().values.mean(axis=0)
            camera_vector = camera_location / np.linalg.norm(camera_location)
            camera_zoom = 2 * points_df.apply(lambda x: np.linalg.norm(x), axis=1).max() / self._axes_range[1]
            camera_center = camera_zoom * camera_vector
            self._camera_view = {"x": camera_center[0], "y": camera_center[1], "z": camera_center[2]}
         except RuntimeWarning as e:
            self._camera_view = {"x": GlobePlot.CAMERA_ZOOM, "y": 0, "z": 0}


   def _load_earth_data(self, land_color=None, ocean_color=None, resolution=None):

      earth_data = self._current_file.parent.parent.parent.joinpath("earth_data")
      self._earth_image = np.load(earth_data.joinpath(f"earth_image_{resolution}.npy"))
      if land_color is not None and ocean_color is not None:
         cutoff = 0.24285714285714285
         land_ocean = self._earth_image > cutoff
         self._earth_image = np.where(land_ocean == True, 1, 0)
         self._earth_colorscale = [[0, ocean_color], [1, land_color]]
      else:
         with open(earth_data.joinpath("earth_colorscale"), "rb") as f:
            self._earth_colorscale = pickle.load(f)


   def _set_earth_points(self):

      theta = np.linspace(0, 2 * np.pi, self._earth_image.shape[0]) + np.pi
      phi = np.linspace(0, np.pi, self._earth_image.shape[1])

      self._earth_x = GlobeMethods.EQUATOR_RADIUS * np.outer(np.cos(theta), np.sin(phi))
      self._earth_y = GlobeMethods.EQUATOR_RADIUS * np.outer(np.sin(theta), np.sin(phi))
      self._earth_z = GlobeMethods.POLAR_RADIUS * np.outer(np.ones(np.size(theta)), np.cos(phi))


   def _set_earth_surface(self, land_color, ocean_color, resolution):

      self._load_earth_data(land_color, ocean_color, resolution)
      self._set_earth_points()

      self._earth_surface = {
         "type": "surface",
         "name": "Earth Surface",
         "x": self._earth_x,
         "y": self._earth_y,
         "z": self._earth_z,
         "surfacecolor": self._earth_image,
         "colorscale": self._earth_colorscale,
         "hoverinfo": "none",
         "showscale": False,
      }


   def _set_axes_range(self, data):

      comm_x_limit = data["comm"][["SenderLocation_X", "ReceiverLocation_X"]].abs().max().max()
      comm_y_limit = data["comm"][["SenderLocation_Y", "ReceiverLocation_Y"]].abs().max().max()
      comm_z_limit = data["comm"][["SenderLocation_Z", "ReceiverLocation_Z"]].abs().max().max()

      platform_x_limit = data["platform"]["Location_X"].abs().max()
      platform_y_limit = data["platform"]["Location_Y"].abs().max()
      platform_z_limit = data["platform"]["Location_Z"].abs().max()

      x_limit = max(comm_x_limit, platform_x_limit)
      y_limit = max(comm_y_limit, platform_y_limit)
      z_limit = max(comm_z_limit, platform_z_limit)

      self._axes_range = [
         -max(x_limit, y_limit, z_limit, GlobeMethods.EQUATOR_RADIUS),
         max(x_limit, y_limit, z_limit, GlobeMethods.EQUATOR_RADIUS)
      ]


   def _set_axes_attributes(self, data):

      self._set_axes_range(data)

      self._axes_attributes = {
         "range": self._axes_range,
         "nticks": 5,
         "showbackground": False,
         "showgrid": False,
         "showline": False,
         "showticklabels": False,
         "ticks":'',
         "title":'',
         "zeroline":False
      }


   def _globe_layout(self):

      globe_layout = {
         "paper_bgcolor":'rgba(0,0,0,0)',
         "plot_bgcolor":'rgba(0,0,0,0)',
         "scene":
         {
            "xaxis": self._axes_attributes,
            "yaxis": self._axes_attributes,
            "zaxis": self._axes_attributes,
            "aspectmode": "cube",
            "camera": {
               "eye": self._camera_view
            }
         }
      }

      return globe_layout