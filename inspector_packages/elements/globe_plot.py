import pickle, warnings
from pathlib import Path
import pandas as pd
from inspector_packages import *
from .globe_methods import GlobeMethods
from ..mission_execution import *

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
      ## track_df = data["track"]
      ## platform_df = data["platform"]

      internal_pts = internal_df[[CommDataColumns.SENDERLOCATION_X, CommDataColumns.SENDERLOCATION_Y, CommDataColumns.SENDERLOCATION_Z]]
      sender_pts = external_df[[CommDataColumns.SENDERLOCATION_X, CommDataColumns.SENDERLOCATION_Y, CommDataColumns.SENDERLOCATION_Z]]
      rcvr_pts = external_df[[CommDataColumns.RECEIVERLOCATION_X, CommDataColumns.RECEIVERLOCATION_Y, CommDataColumns.RECEIVERLOCATION_Z]]
      rcvr_pts = rcvr_pts.rename(columns=
         {CommDataColumns.RECEIVERLOCATION_X: CommDataColumns.SENDERLOCATION_X,
          CommDataColumns.RECEIVERLOCATION_Y: CommDataColumns.SENDERLOCATION_Y,
          CommDataColumns.RECEIVERLOCATION_Z: CommDataColumns.SENDERLOCATION_Z})

      ## platform_pts = platform_df[["Location_X", "Location_Y", "Location_Z"]]
      ## platform_pts = platform_pts.rename(columns=
      ##    {"Location_X": "SenderLocation_X",
      ##     "Location_Y": "SenderLocation_Y",
      ##     "Location_Z": "SenderLocation_Z"})

      points_df = pd.concat([internal_pts, sender_pts, rcvr_pts], ignore_index=True)

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

      x1 = data.execute(f'SELECT MAX(ABS({CommDataColumns.SENDERLOCATION_X})) AS MaxAbsoluteValue FROM {COMM_DATA_TABLE}').fetchone()[0]
      x2 = data.execute(f'SELECT MAX(ABS({CommDataColumns.RECEIVERLOCATION_X})) AS MaxAbsoluteValue FROM {COMM_DATA_TABLE}').fetchone()[0]
      y1 = data.execute(f'SELECT MAX(ABS({CommDataColumns.SENDERLOCATION_Y})) AS MaxAbsoluteValue FROM {COMM_DATA_TABLE}').fetchone()[0]
      y2 = data.execute(f'SELECT MAX(ABS({CommDataColumns.RECEIVERLOCATION_Y})) AS MaxAbsoluteValue FROM {COMM_DATA_TABLE}').fetchone()[0]
      z1 = data.execute(f'SELECT MAX(ABS({CommDataColumns.SENDERLOCATION_Z})) AS MaxAbsoluteValue FROM {COMM_DATA_TABLE}').fetchone()[0]
      z2 = data.execute(f'SELECT MAX(ABS({CommDataColumns.RECEIVERLOCATION_Z})) AS MaxAbsoluteValue FROM {COMM_DATA_TABLE}').fetchone()[0]
      comm_x_limit = max(x1, x2)
      comm_y_limit = max(y1, y2)
      comm_z_limit = max(z1, z2)

      ## platform_x_limit = data.execute(f'SELECT MAX(ABS({PlatformDataColumns.LOCATION_X})) AS MaxAbsoluteValue FROM {PLATFORM_DATA_TABLE}').fetchone()[0]
      ## platform_y_limit = data.execute(f'SELECT MAX(ABS({PlatformDataColumns.LOCATION_Y})) AS MaxAbsoluteValue FROM {PLATFORM_DATA_TABLE}').fetchone()[0]
      ## platform_z_limit = data.execute(f'SELECT MAX(ABS({PlatformDataColumns.LOCATION_Z})) AS MaxAbsoluteValue FROM {PLATFORM_DATA_TABLE}').fetchone()[0]

      ## x_limit = max(comm_x_limit, platform_x_limit)
      ## y_limit = max(comm_y_limit, platform_y_limit)
      ## z_limit = max(comm_z_limit, platform_z_limit)

      self._axes_range = [
         -max(comm_x_limit, comm_y_limit, comm_z_limit, GlobeMethods.EQUATOR_RADIUS),
         max(comm_x_limit, comm_y_limit, comm_z_limit, GlobeMethods.EQUATOR_RADIUS)
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