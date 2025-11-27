from .globe_methods import GlobeMethods
from utils import cli_output
import numpy as np


class GlobeTracks:

   CONTRIBUTION_COLOR = "lightpink"
   MARKER_COLOR = "rgba(255, 182, 193"

   @staticmethod 
   def update_track_events(track_data, platform_data):

      track_events, track_arrows = [], []
      for platform, grp in track_data.groupby("Owning_Platform"):

         recent_track_info = grp.tail(1)
         receiver_location = recent_track_info[["PlatformLocation_X", "PlatformLocation_Y", "PlatformLocation_Z"]].iloc[0].to_numpy()
         master_track_list = recent_track_info["Master_Track_List"].iloc[0].strip().split(" ")
         if recent_track_info["Event_Type"].iloc[0] == "LOCAL_TRACK_DROPPED":
            dropped_track = recent_track_info["Track_ID"].iloc[0]
            time_dropped = recent_track_info["ISODate"].iloc[0]
            master_track_list.remove(dropped_track)
            cli_output.INFO(f"{__class__.__name__}: {dropped_track} dropped at {time_dropped}.")
         for local_track in master_track_list:
            track_grp = grp[grp["Track_ID"] == local_track].tail(1)
            raw_track_list = track_grp["Raw_Tracks"].iloc[0].strip().split(" ")
            for raw_track in raw_track_list:
               contributor_name = raw_track.split(".")[0]
               if contributor_name != "no_tracks":
                  try:
                     contributor_data = platform_data[platform_data["Platform_Name"] == contributor_name]
                     contributor_location = contributor_data[["Location_X", "Location_Y", "Location_Z"]].iloc[0].to_numpy()
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
                  except IndexError as e:
                     cli_output.WARNING(f"{contributor_name} does not exist at time {platform_data['ISODate'].iloc[0]}")

      return track_events, track_arrows