from .globe_methods import GlobeMethods
from utils import cli_output
from ..mission_execution import *
import numpy as np


class GlobeTracks:

   CONTRIBUTION_COLOR = "lightpink"
   MARKER_COLOR = "rgba(255, 182, 193"

   @staticmethod 
   def update_track_events(track_data, platform_data):

      track_events, track_arrows = [], []
      for platform, grp in track_data.groupby(TrackDataColumns.OWNING_PLATFORM):

         recent_track_info = grp.tail(1)
         receiver_location = recent_track_info[[TrackDataColumns.PLATFORMLOCATION_X, TrackDataColumns.PLATFORMLOCATION_Y, TrackDataColumns.PLATFORMLOCATION_Z]].iloc[0].to_numpy()
         master_track_list = recent_track_info[TrackDataColumns.MASTER_TRACK_LIST].iloc[0].strip().split(" ")
         if recent_track_info[SharedColumns.EVENT_TYPE].iloc[0] == "LOCAL_TRACK_DROPPED":
            dropped_track = recent_track_info[TrackDataColumns.TRACK_ID].iloc[0]
            time_dropped = recent_track_info[SharedColumns.ISO_DATE].iloc[0]
            master_track_list.remove(dropped_track)
            cli_output.INFO(f"{__class__.__name__}: {dropped_track} dropped at {time_dropped}.")
         for local_track in master_track_list:
            track_grp = grp[grp[TrackDataColumns.TRACK_ID] == local_track].tail(1)
            raw_track_list = track_grp[TrackDataColumns.RAW_TRACKS].iloc[0].strip().split(" ")
            for raw_track in raw_track_list:
               contributor_name = raw_track.split(".")[0]
               if contributor_name != "no_tracks":
                  try:
                     contributor_data = platform_data.loc[contributor_name]
                     contributor_location = contributor_data[
                        [PlatformDataColumns.LOCATION_X, 
                         PlatformDataColumns.LOCATION_Y, 
                         PlatformDataColumns.LOCATION_Z]].to_numpy()
                     platform_range = np.linalg.norm(receiver_location - contributor_location)
                     line_data = GlobeMethods.create_transmission_line(
                        contributor_location, receiver_location, 
                        contributor_name, platform,
                        platform_range)

                     num_markers = len(line_data["x"]) - 2
                     marker_visibility = [f"{GlobeTracks.MARKER_COLOR}, 1)"] + [f"{GlobeTracks.MARKER_COLOR}, 0)"] * num_markers + [f"{GlobeTracks.MARKER_COLOR}, 1)"]

                     track_events.append(
                        {
                           "type": "scatter3d",
                           "name": "track_contribution",
                           "x": line_data["x"],
                           "y": line_data["y"],
                           "z": line_data["z"],
                           "mode": "lines+markers",
                           "customdata": [f"TRACK_INFO: {contributor_name} >> {platform}" + "<extra></extra>"] * len(line_data["x"]),
                           "hovertemplate":'%{customdata}',
                           "marker":
                           {
                              "size": 5,
                              "color": marker_visibility 
                           },
                           "line": 
                           {
                              "width": 2,
                              "color": GlobeTracks.CONTRIBUTION_COLOR
                           },
                           "opacity": 1,
                           "showlegend": False
                        }
                     )

                     if line_data.get("arrows") is not None:
                        track_arrows.append(
                           {
                              "type": "cone",
                              "name": "contribution_direction",
                              "x": line_data["arrows"]["arrow_x"],
                              "y": line_data["arrows"]["arrow_y"],
                              "z": line_data["arrows"]["arrow_z"],
                              "u": line_data["arrows"]["u"],
                              "v": line_data["arrows"]["v"],
                              "w": line_data["arrows"]["w"],
                              "sizemode": "scaled",
                              "sizeref": line_data["arrows"]["scaling"],
                              "colorscale": [
                                 [0, GlobeTracks.CONTRIBUTION_COLOR],
                                 [1, GlobeTracks.CONTRIBUTION_COLOR],
                              ],
                              "showscale": False,
                              "customdata": [f"TRACK_INFO: {contributor_name} >> {platform}" + "<extra></extra>"] * len(line_data["arrows"]["arrow_x"]),
                              "hovertemplate":'%{customdata}',
                           }
                        )
                  except KeyError as e:
                     cli_output.WARNING(f"{__class__.__name__}: {contributor_name} does not exist at time {platform_data[SharedColumns.ISO_DATE].iloc[0]}")

      return track_events, track_arrows