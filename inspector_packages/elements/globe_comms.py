from datetime import datetime
from .globe_methods import GlobeMethods
from ..mission_execution import *

class GlobeComms:

   TRANSMISSION_RESULT = {
      "Success": {"color_name": "mediumturquoise", "rgb": [72, 209, 204]},
      "Fail": {"color_name": "darkred", "rgb": [139, 0, 0]}
   }
      
   @staticmethod
   def update_external_events(external_df):

      transmissions, transmission_directions = [], []
      for transmission, group in external_df.groupby(
         [CommDataColumns.SENDER_NAME, 
          CommDataColumns.SENDERPART_NAME, 
          CommDataColumns.RECEIVER_NAME, 
          CommDataColumns.RECEIVERPART_NAME]):

         sender_name, _, receiver_name, _ = transmission
         transmission_info, success = GlobeComms._transmission_info_text(transmission, group)
         sender_location = group[
            [CommDataColumns.SENDERLOCATION_X, 
             CommDataColumns.SENDERLOCATION_Y, 
             CommDataColumns.SENDERLOCATION_Z]].iloc[0].to_numpy()
         receiver_location = group[
            [CommDataColumns.RECEIVERLOCATION_X, 
             CommDataColumns.RECEIVERLOCATION_Y, 
             CommDataColumns.RECEIVERLOCATION_Z]].iloc[0].to_numpy()
         platform_range = group[CommDataColumns.SENDERTORCVR_RANGE].values[0]

         line_data = GlobeMethods.create_transmission_line(
            sender_location, receiver_location, 
            sender_name, receiver_name,
            platform_range)
         marker_colors = GlobeComms._marker_color(len(line_data["x"])-2, success)

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
                  "color": GlobeComms.TRANSMISSION_RESULT[success]["color_name"]
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
                     [0, GlobeComms.TRANSMISSION_RESULT[success]["color_name"]],
                     [1, GlobeComms.TRANSMISSION_RESULT[success]["color_name"]],
                  ],
                  "showscale": False,
                  "customdata": [transmission_info] * len(line_data["arrows"]["arrow_x"]),
                  "hovertemplate":'%{customdata}',
               }
            )

      return transmissions, transmission_directions

   @staticmethod
   def update_internal_events(internal_df):

      x, y, z = [], [], []
      internal_events = []
      internal_colors = []
      for sender, group in internal_df.groupby(CommDataColumns.SENDER_NAME):
         x.append(group[CommDataColumns.SENDERLOCATION_X].values[0])
         y.append(group[CommDataColumns.SENDERLOCATION_Y].values[0])
         z.append(group[CommDataColumns.SENDERLOCATION_Z].values[0])

         event_info = '' 
         event_num = 0
         for _, row in group.iterrows():
            event_num += 1
            event_info += f'\
<b>{event_num}. Event Type: {row[SharedColumns.EVENT_TYPE]}</b><br> \
   <b>Platform: {sender}</b><br> \
   Simulation Time: {row[SharedColumns.SIMULATION_TIME]}<br> \
   Platform Parts: {row[CommDataColumns.SENDERPART_NAME]} >> {row["ReceiverPart_Name"]}<br> \
   Message Type: {row[CommDataColumns.MESSAGE_TYPE]}<br> \
   Message Number: {row[CommDataColumns.MESSAGE_SERIALNUMBER]}<br> \
   Message Originator: {row[CommDataColumns.MESSAGE_ORIGINATOR]}<br>'
         event_info += '<extra></extra>' 
         internal_events.append(event_info)

         if not group[group[SharedColumns.EVENT_TYPE] == "MESSAGE_OUTGOING"].empty and \
            not group[group[SharedColumns.EVENT_TYPE] == "MESSAGE_INCOMING"].empty:
            internal_colors.append('goldenrod')
         elif not group[group[SharedColumns.EVENT_TYPE] == "MESSAGE_OUTGOING"].empty:
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

   @staticmethod
   def _transmission_info_text(transmission, group):

      sender, sender_part, receiver, receiver_part = transmission

      transmission_info = ''
      transmission_num = 0
      transmission_result = "Success"
      for _, row in group.iterrows():
         transmission_num += 1
         transmission_info += f'\
<b>{transmission_num}. Event Type: {row[SharedColumns.EVENT_TYPE]}</b><br> \
   <b>Sender: {sender} >> Receiver: {receiver}</b><br> \
   Simulation Time: {row[SharedColumns.SIMULATION_TIME]}<br> \
   Platform Parts: {sender_part} >> {receiver_part}<br> \
   Message Type: {row[CommDataColumns.MESSAGE_TYPE]}<br> \
   Message Number: {row[CommDataColumns.MESSAGE_SERIALNUMBER]}<br> \
   Message Originator: {row[CommDataColumns.MESSAGE_ORIGINATOR]}<br>'
         if row[CommDataColumns.COMMINTERACTION_FAILEDSTATUS] != "Does Not Exist":
            transmission_result = "Fail"
            transmission_info += f'    Failure Reason: {row[CommDataColumns.COMMINTERACTION_FAILEDSTATUS]}<br>'
      transmission_info += '<extra></extra>' 

      return transmission_info, transmission_result


   @staticmethod
   def _marker_color(num_markers, success):

      rgb = GlobeComms.TRANSMISSION_RESULT[success]["rgb"]
      marker_color = f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}"
      marker_visibility = [f"{marker_color}, 1)"] + [f"{marker_color}, 0)"] * num_markers + [f"{marker_color}, 1)"]

      return marker_visibility