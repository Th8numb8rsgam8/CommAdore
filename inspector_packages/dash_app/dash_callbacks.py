import json
from . import *
from ..elements import *
from inspector_packages import *
from datetime import datetime
import pandas as pd
from dash import no_update, ctx, Input, Output, State
from .dash_layout import DashLayout

import pdb

class DashCallbacks:

   def __init__(self, 
      data,
      land_color=None, 
      ocean_color=None, 
      resolution=None, 
      classification=None,
      cesium_config=None,
      use_cesium=False):

      self._data = data
      self._timestamps = data["comm"]["Timestamp"].unique()

      self._current_frame = {"comm": data["comm"], "track": data["track"]} 
      self._cesium_config = cesium_config

      self._network_plot = NetworkPlot()
      self._globe_platforms = GlobePlatforms(data["platform"])
      self._dashboard = DashLayout(
         data,
         self._timestamps, classification, 
         self._network_plot.figure_name, 
         cesium_config,
         use_cesium)
      self._app = self._dashboard.get_app()

      if use_cesium:
         self._cesium_globe = CesiumJSGlobe(self._app)
      else:
         self._globe_plot = GlobePlot(data, land_color, ocean_color, resolution)

      self._internal_messages = ["MESSAGE_INTERNAL", "MESSAGE_INCOMING", "MESSAGE_OUTGOING"]
      self._external_messages = ["MESSAGE_DELIVERY_ATTEMPT", "MESSAGE_RECEIVED"]

      self._plots_options = {
         "Bar Plot": {"Graph": self._dashboard.initialize_barplot(), "Options": self._dashboard.initialize_barplot_options()},
         "Network Plot": {"Graph": self._dashboard.initialize_network_plot(), "Options": self._dashboard.initialize_network_options()}
      }

      self._filter_options = {
         "Event_Type": self._data["comm"]["Event_Type"].unique(),
         "Message_SerialNumber": self._data["comm"]["Message_SerialNumber"].unique(),
         "Message_Originator": self._data["comm"]["Message_Originator"].unique(),
         "Message_Type": self._data["comm"]["Message_Type"].unique(),
         "Sender_Name": self._data["comm"]["Sender_Name"].unique(),
         "Sender_Side": self._data["comm"]["Sender_Side"].unique(),
         "Sender_Type": self._data["comm"]["Sender_Type"].unique(),
         "Sender_BaseType": self._data["comm"]["Sender_BaseType"].unique(),
         "SenderPart_Name": self._data["comm"]["SenderPart_Name"].unique(),
         "SenderPart_Type": self._data["comm"]["SenderPart_Type"].unique(),
         "SenderPart_BaseType": self._data["comm"]["SenderPart_BaseType"].unique(),
         "Receiver_Name": self._data["comm"]["Receiver_Name"].unique(),
         "Receiver_Side": self._data["comm"]["Receiver_Side"].unique(),
         "Receiver_Type": self._data["comm"]["Receiver_Type"].unique(),
         "Receiver_BaseType": self._data["comm"]["Receiver_BaseType"].unique(),
         "ReceiverPart_Name": self._data["comm"]["ReceiverPart_Name"].unique(),
         "ReceiverPart_Type": self._data["comm"]["ReceiverPart_Type"].unique(),
         "ReceiverPart_BaseType": self._data["comm"]["ReceiverPart_BaseType"].unique()
      }

      self._empty_plot = {
         "paper_bgcolor":'rgba(0,0,0,0)',
         "plot_bgcolor":'rgba(0,0,0,0)',
         "xaxis": 
         {
            "showgrid": False,
            "showticklabels": False,
            "ticks":'',
            "zeroline":False
         },
         "yaxis": 
         {
            "showgrid": False,
            "showticklabels": False,
            "ticks":'',
            "zeroline":False
         }
      }

      if use_cesium:
         self._define_cesium_filter_callback()
      else:
         self._define_filter_callback()

      self._define_barplot_callback()
      self._define_network_plot_callback()
      self._define_plot_select_callback()
      self._define_filter_storage_callback()
      self._define_dropdown_options_callback()
      self._define_time_button_callback()
      self._define_time_label_callback()

   @property
   def app(self):

      return self._app

   def _get_current_data(self, value):

      frame = self._current_frame

      if ctx.triggered_id != TIME_SLIDER:
         self._timestamps = frame["comm"]["Timestamp"].unique()

      if ctx.triggered_id != TIME_SLIDER:
         comm_frame = frame["comm"][frame["comm"]["Timestamp"] == self._timestamps[0]]
         platform_states = self._globe_platforms.get_platform_states(self._timestamps[0])
         t = platform_states["Timestamp"].iloc[0]
         track_frame = frame["track"][frame["track"]["Timestamp"] <= t]
         current_time = datetime.utcfromtimestamp(self._timestamps[0]).strftime("%H:%M:%S.%f")[:-3]
      else:
         comm_frame = frame["comm"][frame["comm"]["Timestamp"] == value]
         platform_states = self._globe_platforms.get_platform_states(value)
         t = platform_states["Timestamp"].iloc[0]
         track_frame = frame["track"][frame["track"]["Timestamp"] <= t]
         current_time = datetime.utcfromtimestamp(value).strftime("%H:%M:%S.%f")[:-3]

      internal = comm_frame[comm_frame["Event_Type"].isin(self._internal_messages)]
      external = comm_frame[comm_frame["Event_Type"].isin(self._external_messages)]

      current_data = {
         "comm": {"internal": internal, "external": external},
         "track": track_frame,
         "platform": platform_states
         }

      return (current_data, current_time)

   def _filter_dataframe(self):

      comm_df = self._data["comm"]
      for key, val in self._filter_options.items():
         if val is not None and len(val) != 0:
            comm_df = comm_df[comm_df[key].isin(val)]

      return {"comm": comm_df, "track": self._data["track"]}

   def _define_time_label_callback(self):

      @self._app.callback(
         Output(TIME_LABEL, "children"),
         Input(TIME_SLIDER, "value"),
         Input(RADIOS, 'value')
      )
      def _write_time_label(value, radio_val):

         current_time = datetime.utcfromtimestamp(value).strftime("%H:%M:%S.%f")[:-3]

         if radio_val:
            return f"Current Time: {current_time}"
         else:
            return "Plots not tied to time!"


   def _define_barplot_callback(self):

      @self._app.callback(
         Output(BAR_GRAPH, "figure"),
         Input(TIME_SLIDER, "value"),
         Input(SUBPLOT_CATEGORY, "value"),
         Input(BAR_GRAPH_CATEGORY, "value"),
         Input(BAR_STACK_CATEGORY, "value"),
         Input(DISPLAY_MEMORY, "data"),
         Input(RADIOS, 'value')
      )
      def update_barplots(
         time_value, subplot_category, 
         bar_graph_category, bar_stack_category,
         filter_data, radio_val):

         frame = self._current_frame["comm"]

         if radio_val:
            frame = frame[frame["Timestamp"] == time_value]

         if not frame.empty:
            return BarPlot.generate_barplots(frame, subplot_category, bar_graph_category, bar_stack_category)
         else:
            return go.Figure({"data": None, "layout": self._empty_plot})


   def _define_network_plot_callback(self):

         @self._app.callback(
            Output(self._network_plot.figure_name, "figure"),
            Input(TIME_SLIDER, "value"),
            Input(NETWORK_LAYOUT, "value"),
            Input(DISPLAY_MEMORY, "data"),
            Input(RADIOS, 'value'),
            Input(QUEUE_INFO_TOGGLE, 'value')
         )
         def update_network_plot(time_value, network_layout, filter_data, radio_val, queue_info_toggle):

            comm_df = self._current_frame["comm"]
            track_df = None

            if radio_val:
               comm_df = comm_df[comm_df["Timestamp"] == time_value]
               track_df = self._current_frame["track"][self._current_frame["track"]["Timestamp"] <= time_value]
            else: # radio_val = NO
               if ctx.triggered_id == TIME_SLIDER:
                  return no_update

            comm_df = comm_df[comm_df["Event_Type"].isin(self._external_messages)]
            if not comm_df.empty or (radio_val and not track_df.empty):
               return self._network_plot.generate_network_figure(
                  comm_df, 
                  track_df, 
                  self._globe_platforms.get_platform_states(time_value),
                  network_layout, 
                  self._empty_plot, 
                  self._data["queues"] if (radio_val and queue_info_toggle) else None)
            else:
               return go.Figure({"data": None, "layout": self._empty_plot})


   def _define_plot_select_callback(self):

      @self._app.callback(
         Output(PLOTS_AREA, "children"),
         Output(PLOT_FILTERS, "children"),
         Input(PLOT_OPTIONS, "value")
      )
      def select_plot(plot_option):

         option = self._plots_options[plot_option]

         return option["Graph"], option["Options"]


   def _define_time_button_callback(self):

      @self._app.callback(
         Output(TIME_SLIDER, 'value', allow_duplicate=True),
         Input(PREVIOUS_TIME, 'n_clicks'),
         Input(NEXT_TIME, 'n_clicks'),
         State(TIME_SLIDER, 'value'),
         prevent_initial_call=True
      )
      def shift_time(previous_time, next_time, current_time):

         if current_time is None:
            return self._timestamps[0]

         current_idx = np.where(self._timestamps == current_time)[0][0]

         if ctx.triggered_id == PREVIOUS_TIME:
            if current_idx != 0:
               return self._timestamps[current_idx-1]
            else:
               return self._timestamps[0]

         if ctx.triggered_id == NEXT_TIME:
            if current_idx != self._timestamps.shape[0] - 1:
               return self._timestamps[current_idx+1]
            else:
               return self._timestamps[-1]


   def _define_filter_callback(self):

      @self._app.callback(
         [Output(GLOBE_GRAPH, 'figure'),
         # Output('empty-dataframe-message', 'style'), Output('empty-dataframe-message', 'children'),
         Output(TIME_SLIDER, 'min'), Output(TIME_SLIDER, 'max'),
         Output(TIME_SLIDER, 'value'), Output(TIME_SLIDER, 'marks')],
         Input(TIME_SLIDER, 'value'),
         Input(DISPLAY_MEMORY, "data"),
         # State('empty-dataframe-message', 'style')
      )
      def filter_frame(value, filter_data):

         current_data, current_time = self._get_current_data(value)
         external = current_data["comm"]["external"]
         internal = current_data["comm"]["internal"]
         track_data = current_data["track"]
         platform_data = current_data["platform"]

         update = []
         if not track_data.empty:
            track_events, track_arrows = GlobeTracks.update_track_events(track_data, platform_data)
            update.extend(track_events)
            update.extend(track_arrows)

         if not external.empty:
            transmission_plots, transmission_directions = GlobeComms.update_external_events(external, current_time)
            update.extend(transmission_directions)
            update.extend(transmission_plots)

         if not internal.empty:
            new_plot = GlobeComms.update_internal_events(internal, current_time)
            update.append(new_plot)

         # if platform_data is not None:
         #    self._globe_platforms.update_platform_positions()
         #    pdb.set_trace()

         self._globe_plot.set_camera_view(current_data)
         fig = self._globe_plot.build_earth_figure(update)

         if ctx.triggered_id != TIME_SLIDER and len(self._timestamps) != 0:
            slider_marks = {}
            for val in self._timestamps:
               slider_marks[val] = '' 
            return fig, self._timestamps[0], self._timestamps[-1], self._timestamps[0], slider_marks
         else:
            return fig, no_update, no_update, no_update, no_update

   def _define_cesium_filter_callback(self):

      @self._app.callback(
         [Output(CESIUM_EXTERNAL, 'data'), Output(CESIUM_INTERNAL, 'data'), 
          Output(CESIUM_TRACKS, 'data'), Output(CESIUM_CAMERA, 'data'),
         Output(TIME_SLIDER, 'min'), Output(TIME_SLIDER, 'max'),
         Output(TIME_SLIDER, 'value'), Output(TIME_SLIDER, 'marks')],
         Input(TIME_SLIDER, 'value'),
         Input(DISPLAY_MEMORY, 'data'),
      )
      def cesium_globe_callback(value, filter_data):

         current_data, current_time = self._get_current_data(value)
         external = current_data["comm"]["external"]
         internal = current_data["comm"]["internal"]
         track_data = current_data["track"]
         platform_data = current_data["platform"]

         track_json = {}
         if not track_data.empty:
            track_json = CesiumJSGlobe.get_track_details(track_data, platform_data)

         external_json = {}
         if not external.empty:
            group_idx = 1
            for transmission, group in external.groupby(["Sender_Name", "SenderPart_Name", "Receiver_Name", "ReceiverPart_Name"]):

               sender_name, _, receiver_name, _ = transmission
               sender_location = np.array([
                  group["SenderLocation_X"].values[0], 
                  group["SenderLocation_Y"].values[0], 
                  group["SenderLocation_Z"].values[0]])

               receiver_location = np.array([
                  group["ReceiverLocation_X"].values[0], 
                  group["ReceiverLocation_Y"].values[0], 
                  group["ReceiverLocation_Z"].values[0]])
                           
               platform_range = group["SenderToRcvr_Range"].values[0]

               x, y, z = CesiumJSGlobe.get_line_points(sender_name, sender_location, receiver_name, receiver_location, platform_range)
               external_json[f"group_{group_idx}"] = {
                  "transmission": list(transmission), 
                  "info": group.to_dict(),
                  "line_points": {"x": x, "y": y, "z": z},
                  "current_time": current_time
                  }

               group_idx += 1

         internal_json = {}
         if not internal.empty:
            for sender, group in internal.groupby("Sender_Name"):
               internal_json[sender] = {
                  "info": group.to_dict(),
                  "current_time": current_time
               }

         camera_view = CesiumJSGlobe.set_camera_view(internal, external)

         if ctx.triggered_id != TIME_SLIDER and len(self._timestamps) != 0:
            slider_marks = {}
            for val in self._timestamps:
               slider_marks[val] = '' 
            return [
               json.dumps(external_json), 
               json.dumps(internal_json), 
               json.dumps(track_json),
               json.dumps(camera_view), 
               self._timestamps[0], 
               self._timestamps[-1], 
               self._timestamps[0], 
               slider_marks]
         else:
            return [
               json.dumps(external_json), 
               json.dumps(internal_json), 
               json.dumps(track_json),
               json.dumps(camera_view), 
               no_update, 
               no_update, 
               no_update, 
               no_update]


   def _define_filter_storage_callback(self):

      @self._app.callback(
         Output(FILTER_MEMORY, "data", allow_duplicate=True),
         Input(EVENT_TYPE, "value"),
         Input(MSG_SERIAL_NUMBER, "value"),
         Input(MSG_ORIGINATOR, "value"),
         Input(MSG_TYPE, "value"),
         Input(SENDER_NAME, "value"),
         Input(SENDER_SIDE, "value"),
         Input(SENDER_TYPE, "value"),
         Input(SENDER_BASETYPE, "value"),
         Input(SENDER_PART, "value"),
         Input(SENDER_PART_TYPE, "value"),
         Input(SENDER_PART_BASETYPE, "value"),
         Input(RECEIVER_NAME, "value"),
         Input(RECEIVER_SIDE, "value"),
         Input(RECEIVER_TYPE, "value"),
         Input(RECEIVER_BASETYPE, "value"),
         Input(RECEIVER_PART, "value"),
         Input(RECEIVER_PART_TYPE, "value"),
         Input(RECEIVER_PART_BASETYPE, "value"),
         prevent_initial_call=True
      )
      def store_filter_info(
         evt_type, 
         msg_serial_number, msg_originator, msg_type,
         sender_name, sender_side, sender_type, sender_basetype,
         sender_part, sender_part_type, sender_part_basetype,
         rcvr_name, rcvr_side, rcvr_type, rcvr_basetype, 
         rcvr_part, rcvr_part_type, rcvr_part_basetype):

         self._filter_options["Event_Type"] = evt_type
         self._filter_options["Message_SerialNumber"] = msg_serial_number
         self._filter_options["Message_Originator"] = msg_originator
         self._filter_options["Message_Type"] = msg_type
         self._filter_options["Sender_Name"] = sender_name
         self._filter_options["Sender_Side"] = sender_side
         self._filter_options["Sender_Type"] = sender_type
         self._filter_options["Sender_BaseType"] = sender_basetype
         self._filter_options["SenderPart_Name"] = sender_part
         self._filter_options["SenderPart_Type"] = sender_part_type
         self._filter_options["SenderPart_BaseType"] = sender_part_basetype
         self._filter_options["Receiver_Name"] = rcvr_name
         self._filter_options["Receiver_Side"] = rcvr_side
         self._filter_options["Receiver_Type"] = rcvr_type
         self._filter_options["Receiver_BaseType"] = rcvr_basetype
         self._filter_options["ReceiverPart_Name"] = rcvr_part
         self._filter_options["ReceiverPart_Type"] = rcvr_part_type
         self._filter_options["ReceiverPart_BaseType"] = rcvr_part_basetype

         self._current_frame = self._filter_dataframe()

         data = {"frame_filtered": True}

         return data

   
   def _define_dropdown_options_callback(self):

      @self._app.callback(
         [Output(EVENT_TYPE, "options"),
         Output(MSG_SERIAL_NUMBER, "options"),
         Output(MSG_ORIGINATOR, "options"),
         Output(MSG_TYPE, "options"),
         Output(SENDER_NAME, "options"),
         Output(SENDER_SIDE, "options"),
         Output(SENDER_TYPE, "options"),
         Output(SENDER_BASETYPE, "options"),
         Output(SENDER_PART, "options"),
         Output(SENDER_PART_TYPE, "options"),
         Output(SENDER_PART_BASETYPE, "options"),
         Output(RECEIVER_NAME, "options"),
         Output(RECEIVER_SIDE, "options"),
         Output(RECEIVER_TYPE, "options"),
         Output(RECEIVER_BASETYPE, "options"),
         Output(RECEIVER_PART, "options"),
         Output(RECEIVER_PART_TYPE, "options"),
         Output(RECEIVER_PART_BASETYPE, "options")],
         Output(DISPLAY_MEMORY, "data"),
         Input(FILTER_MEMORY, "data"),
         prevent_initial_call=True
      )
      def update_dropdown_options(filter_data):

         options = [] 
         for column in self._filter_options:
            options.append(self._current_frame["comm"][column].unique())

         options.append(True)
         
         return options