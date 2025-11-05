import sys
import warnings
import numpy as np
from .globe_methods import GlobeMethods
from utils import cli_output


class GlobeComms:

   def __init__(self):

      self._transmission_result = {
         "Success": {"color_name": "mediumturquoise", "rgb": [72, 209, 204]},
         "Fail": {"color_name": "darkred", "rgb": [139, 0, 0]}
      }

      self._transmission_arrows = [
          {"range": [0, 1000], "scaling": None, "interval": None},
          {"range": [1000, 10000], "scaling": 0.8, "interval":  100},
          {"range": [10000, 50000], "scaling": 0.77, "interval":  1000},
          {"range": [50000, 100000], "scaling": 0.74, "interval":  5000},
          {"range": [100000, 500000], "scaling": 0.71, "interval":  10000},
          {"range": [500000, 1000000], "scaling": 0.68, "interval":  50000},
          {"range": [1000000, 5000000], "scaling": 0.65, "interval":  100000},
          {"range": [5000000, 10000000], "scaling": 0.4, "interval":  500000},
          {"range": [10000000, 50000000], "scaling": 0.35, "interval":  1000000},
          {"range": [50000000, sys.maxsize], "scaling": 0.3, "interval":  5000000},
      ]


   def update_external_events(self, external_df, current_time):

      transmissions, transmission_directions = [], []
      for transmission, group in external_df.groupby(["Sender_Name", "SenderPart_Name", "Receiver_Name", "ReceiverPart_Name"]):

         transmission_info, success = self._transmission_info_text(current_time, transmission, group)
         line_data = self._create_transmission_line(group)
         marker_colors = self._marker_color(len(line_data["x"])-2, success)

         transmissions.append(
            {
               "type": "scatter3d",
               "name": "external",
               "x": line_data["x"],
               "y": line_data["y"],
               "z": line_data["z"],
               "mode": "lines+markers",
               "customdata": [transmission_info] * len(line_data["x"]),
               "hovertemplate":'%{customdata}',
               "marker":
               {
                  "size": 5,
                  "color": marker_colors
               },
               "line": 
               {
                  "width": 1,
                  "color": self._transmission_result[success]["color_name"]
               },
               "opacity": 1,
               "showlegend": False
            }
         )

         if line_data.get("arrows") is not None:
            transmission_directions.append(
               {
                  "type": "cone",
                  "name": "transmission_direction",
                  "x": line_data["arrows"]["arrow_x"],
                  "y": line_data["arrows"]["arrow_y"],
                  "z": line_data["arrows"]["arrow_z"],
                  "u": line_data["arrows"]["u"],
                  "v": line_data["arrows"]["v"],
                  "w": line_data["arrows"]["w"],
                  "sizemode": "scaled",
                  "sizeref": line_data["arrows"]["scaling"],
                  "colorscale": [
                     [0, self._transmission_result[success]["color_name"]],
                     [1, self._transmission_result[success]["color_name"]],
                  ],
                  "showscale": False,
                  "customdata": [transmission_info] * len(line_data["arrows"]["arrow_x"]),
                  "hovertemplate":'%{customdata}',
               }
            )

      return transmissions, transmission_directions


   def update_internal_events(self, internal_df, current_time):

      x, y, z = [], [], []
      internal_events = []
      internal_colors = []
      for sender, group in internal_df.groupby("Sender_Name"):
         x.append(group["SenderLocation_X"].values[0])
         y.append(group["SenderLocation_Y"].values[0])
         z.append(group["SenderLocation_Z"].values[0])

         event_info = '' 
         event_info = f'Time (H:M:S): {current_time}<br>'
         event_info += f'Platform: {sender}<br>'
         event_num = 0
         for _, row in group.iterrows():
            event_num += 1
            event_info += f'\
{event_num}. Event Type: {row["Event_Type"]}<br> \
   Platform Parts: {row["SenderPart_Name"]} >> {row["ReceiverPart_Name"]}<br> \
   Message Type: {row["Message_Type"]}<br> \
   Message Number: {row["Message_SerialNumber"]}<br> \
   Message Originator: {row["Message_Originator"]}<br>'
         event_info += '<extra></extra>' 
         internal_events.append(event_info)

         if not group[group["Event_Type"] == "MESSAGE_OUTGOING"].empty and \
            not group[group["Event_Type"] == "MESSAGE_INCOMING"].empty:
            internal_colors.append('goldenrod')
         elif not group[group["Event_Type"] == "MESSAGE_OUTGOING"].empty:
            internal_colors.append('cornflowerblue')
         elif not group[group["Event_Type"] == "MESSAGE_INCOMING"].empty:
            internal_colors.append('mediumspringgreen')
         else:
            internal_colors.append('salmon')

      updated_plot = {
         "type": "scatter3d",
         "name": "internal",
         "x": x,
         "y": y,
         "z": z,
         "mode": "markers",
         "customdata": internal_events,
         "hovertemplate":'%{customdata}',
         "marker": 
         {
            "size": 5,
            "color": internal_colors 
         },
         "opacity": 1,
         "showlegend": False
      }

      return updated_plot


   def _transmission_info_text(self, current_time, transmission, group):

      sender, sender_part, receiver, receiver_part = transmission

      transmission_info = ''
      transmission_info = f'Time (H:M:S): {current_time}<br>'
      transmission_info += f'Sender: {sender} >> Receiver: {receiver}<br>'
      transmission_num = 0
      transmission_result = "Success"
      for _, row in group.iterrows():
         transmission_num += 1
         transmission_info += f'\
<b>{transmission_num}. Event Type: {row["Event_Type"]}</b><br> \
   Platform Parts: {sender_part} >> {receiver_part}<br> \
   Message Type: {row["Message_Type"]}<br> \
   Message Number: {row["Message_SerialNumber"]}<br> \
   Message Originator: {row["Message_Originator"]}<br>'
         if row["CommInteraction_FailedStatus"] != "Does Not Exist":
            transmission_result = "Fail"
            transmission_info += f'    Failure Reason: {row["CommInteraction_FailedStatus"]}<br>'
      transmission_info += '<extra></extra>' 

      return transmission_info, transmission_result


   def _create_transmission_line(self, group):

      line_data = {}
      sender_location = np.array([
         group["SenderLocation_X"].values[0], 
         group["SenderLocation_Y"].values[0], 
         group["SenderLocation_Z"].values[0]])

      receiver_location = np.array([
         group["ReceiverLocation_X"].values[0], 
         group["ReceiverLocation_Y"].values[0], 
         group["ReceiverLocation_Z"].values[0]])
         
      platform_range = group["SenderToRcvr_Range"].values[0]

      interval = None
      scaling = None
      for rng_step in self._transmission_arrows:
          min_rng, max_rng = rng_step["range"]
          if min_rng < platform_range <= max_rng:
              interval = rng_step["interval"]
              scaling = rng_step["scaling"]
              break

      with warnings.catch_warnings():
         warnings.filterwarnings('error', category=RuntimeWarning)
         try:
            num_arrows, remainder = divmod(platform_range, interval if interval is not None else platform_range + 1)
            delta = (0.5 * remainder / platform_range) * (receiver_location - sender_location)
            first_arrow = sender_location + delta
            last_arrow = receiver_location - delta

            if GlobeMethods.los_hits_horizon(sender_location, receiver_location):
               x, y, z = GlobeMethods.get_curve_points_on_sphere(first_arrow, last_arrow, int(num_arrows) if num_arrows != 0 else 10)
            else:
               x, y, z = GlobeMethods.get_points_on_line_segment(first_arrow, last_arrow, int(num_arrows) if num_arrows != 0 else 10)

            line_data.update({
               "x": [sender_location[0]] + x + [receiver_location[0]],
               "y": [sender_location[1]] + y + [receiver_location[1]],
               "z": [sender_location[2]] + z + [receiver_location[2]],
            })

            if num_arrows != 0:
               u, v, w = [], [], []
               arrow_x, arrow_y, arrow_z = [], [], []
               for i in range(int(num_arrows)):
                  pt1 = np.array([x[i], y[i], z[i]])
                  pt2 = np.array([x[i+1], y[i+1], z[i+1]])
                  vector = pt2 - pt1
                  arrow_center = pt1 + 0.5 * vector
                  arrow_x.append(arrow_center[0])
                  arrow_y.append(arrow_center[1])
                  arrow_z.append(arrow_center[2])
                  u.append(vector[0])
                  v.append(vector[1])
                  w.append(vector[2])
               arrows = {
                  "scaling": scaling,
                  "arrow_x": arrow_x,
                  "arrow_y": arrow_y,
                  "arrow_z": arrow_z,
                  "u": u, "v": v, "w": w
               }
               line_data["arrows"] = arrows

         except RuntimeWarning as e:
            cli_output.WARNING(f"NO transmission line from {group['Sender_Name'].iloc[0]} to {group['Receiver_Name'].iloc[0]}.")
            line_data.update({
               "x": [sender_location[0], receiver_location[0]],
               "y": [sender_location[1], receiver_location[1]],
               "z": [sender_location[2], receiver_location[2]],
            })
            return line_data

      return line_data


   def _marker_color(self, num_markers, success):

      rgb = self._transmission_result[success]["rgb"]
      marker_color = f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}"
      marker_visibility = [f"{marker_color}, 1)"] + [f"{marker_color}, 0)"] * num_markers + [f"{marker_color}, 1)"]

      return marker_visibility