import json
from . import *
from ..elements import *
from inspector_packages import *
import pandas as pd
from dash import no_update, ctx, Input, Output, State
from ..mission_execution import *
from .dash_layout import DashLayout
from utils import timer

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
      sim_times = pd.read_sql_query(f'SELECT DISTINCT {SharedColumns.SIMULATION_TIME} FROM {COMM_DATA_TABLE}', self._data)
      self._timestamps = sim_times[SharedColumns.SIMULATION_TIME].values

      self._cesium_config = cesium_config

      self._network_plot = NetworkPlot()

      self._dashboard = DashLayout(
         data,
         self._timestamps, classification, 
         self._network_plot.figure_name, 
         cesium_config, use_cesium)

      self._app = self._dashboard.get_app()

      if use_cesium:
         self._cesium_globe = CesiumJSGlobe(self._app)
      else:
         self._globe_plot = GlobePlot(self._data, land_color, ocean_color, resolution)

      self._internal_messages = ["MESSAGE_INTERNAL", "MESSAGE_INCOMING", "MESSAGE_OUTGOING"]
      self._external_messages = ["MESSAGE_DELIVERY_ATTEMPT", "MESSAGE_RECEIVED"]

      self._comm_filter_options = {
         SharedColumns.EVENT_TYPE: self._get_unique_values(SharedColumns.EVENT_TYPE, COMM_DATA_TABLE),
         CommDataColumns.MESSAGE_SERIALNUMBER: self._get_unique_values(CommDataColumns.MESSAGE_SERIALNUMBER, COMM_DATA_TABLE),
         CommDataColumns.MESSAGE_ORIGINATOR: self._get_unique_values(CommDataColumns.MESSAGE_ORIGINATOR, COMM_DATA_TABLE),
         CommDataColumns.MESSAGE_TYPE: self._get_unique_values(CommDataColumns.MESSAGE_TYPE, COMM_DATA_TABLE),
         CommDataColumns.SENDER_NAME: self._get_unique_values(CommDataColumns.SENDER_NAME, COMM_DATA_TABLE),
         CommDataColumns.SENDER_SIDE: self._get_unique_values(CommDataColumns.SENDER_SIDE, COMM_DATA_TABLE),
         CommDataColumns.SENDER_TYPE: self._get_unique_values(CommDataColumns.SENDER_TYPE, COMM_DATA_TABLE),
         CommDataColumns.SENDER_BASETYPE: self._get_unique_values(CommDataColumns.SENDER_BASETYPE, COMM_DATA_TABLE),
         CommDataColumns.SENDERPART_NAME: self._get_unique_values(CommDataColumns.SENDERPART_NAME, COMM_DATA_TABLE),
         CommDataColumns.SENDERPART_TYPE: self._get_unique_values(CommDataColumns.SENDERPART_TYPE, COMM_DATA_TABLE),
         CommDataColumns.SENDERPART_BASETYPE: self._get_unique_values(CommDataColumns.SENDERPART_BASETYPE, COMM_DATA_TABLE),
         CommDataColumns.RECEIVER_NAME: self._get_unique_values(CommDataColumns.RECEIVER_NAME, COMM_DATA_TABLE),
         CommDataColumns.RECEIVER_SIDE: self._get_unique_values(CommDataColumns.RECEIVER_SIDE, COMM_DATA_TABLE),
         CommDataColumns.RECEIVER_TYPE: self._get_unique_values(CommDataColumns.RECEIVER_TYPE, COMM_DATA_TABLE),
         CommDataColumns.RECEIVER_BASETYPE: self._get_unique_values(CommDataColumns.RECEIVER_BASETYPE, COMM_DATA_TABLE),
         CommDataColumns.RECEIVERPART_NAME: self._get_unique_values(CommDataColumns.RECEIVERPART_NAME, COMM_DATA_TABLE),
         CommDataColumns.RECEIVERPART_TYPE: self._get_unique_values(CommDataColumns.RECEIVERPART_TYPE, COMM_DATA_TABLE),
         CommDataColumns.RECEIVERPART_BASETYPE: self._get_unique_values(CommDataColumns.RECEIVERPART_BASETYPE, COMM_DATA_TABLE)
      }

      self._filter_statements = [
         f'''{key} IN ('{"', '".join(map(str, vals))}')''' 
         for key, vals in self._comm_filter_options.items()
         if vals is not None and len(vals) != 0]

      self._empty_plot = {
         "paper_bgcolor":'rgba(0,0,0,0)',
         "plot_bgcolor":'rgba(0,0,0,0)',
         "xaxis": 
         {
            "showgrid": False,
            "showticklabels": False,
            "ticks":'',
            "zeroline": False
         },
         "yaxis": 
         {
            "showgrid": False,
            "showticklabels": False,
            "ticks":'',
            "zeroline": False
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
      self._define_single_time_button_callback()
      self._define_time_button_callback()
      self._define_boolean_switch_callback()
      self._define_time_label_callback()

   @property
   def app(self):

      return self._app

   def _get_unique_values(self, col_name, table_name):
      values = pd.read_sql_query(
         f'SELECT DISTINCT {col_name} FROM {table_name}', 
         self._data)[col_name].values

      return values

   def _get_current_data(self, value, is_single_time):

      if ctx.triggered_id != TIME_SLIDER and ctx.triggered_id != TIME_RANGE_SLIDER:
         use_filter = len(self._filter_statements) > 0
         query = f'''
            SELECT DISTINCT {SharedColumns.SIMULATION_TIME} 
            FROM {COMM_DATA_TABLE}
            {f"WHERE {' AND '.join(self._filter_statements)}" if use_filter else ""}
            '''
         sim_times = pd.read_sql_query(query, self._data)
         self._timestamps = sim_times[SharedColumns.SIMULATION_TIME].values

      if is_single_time:
         if ctx.triggered_id != TIME_SLIDER:
            comm_frame = self._filter_comm_table(self._timestamps[0])
         else:
            comm_frame = self._filter_comm_table(value)
      else:
         if ctx.triggered_id != TIME_RANGE_SLIDER:
            upper_limit = self._timestamps[-1] if len(self._timestamps) <= SLIDER_UPPER_LIMIT else self._timestamps[SLIDER_UPPER_LIMIT-1]
            comm_frame = self._filter_comm_table((self._timestamps[0], upper_limit), range_slider=True)
         else:
            comm_frame = self._filter_comm_table(value, range_slider=True)

      internal = comm_frame[comm_frame[SharedColumns.EVENT_TYPE].isin(self._internal_messages)]
      external = comm_frame[comm_frame[SharedColumns.EVENT_TYPE].isin(self._external_messages)]

      current_data = {"comm": {"internal": internal, "external": external}}

      return current_data

   def _filter_comm_table(self, time_val, range_slider=False):

      if range_slider:
         lower_limit, upper_limit = time_val
         time_filter = f'{SharedColumns.SIMULATION_TIME} BETWEEN {lower_limit} AND {upper_limit}'
      else:
         time_filter = f'{SharedColumns.SIMULATION_TIME} = {time_val}'

      use_filter = len(self._filter_statements) > 0
      query = f'''
         SELECT *
         FROM {COMM_DATA_TABLE}
         WHERE {time_filter}
         {f"AND {' AND '.join(self._filter_statements)}" if use_filter else ""}
         '''
      frame = pd\
         .read_sql_query(
            sql=query, 
            con=self._data, 
            index_col=SharedColumns.EVENT_ID)\
         .replace('nan', np.nan)\
         .astype(PANDAS_COMM_DATA_TYPES)

      return frame

   def _update_options(self, col_name, data_type):

      use_filter = len(self._filter_statements) > 0
      query = f'''
         SELECT DISTINCT {col_name}
         FROM {eval(f'{data_type}_DATA_TABLE')}
         {f"WHERE {' AND '.join(self._filter_statements)}" if use_filter else ""}
         '''
      options = pd.read_sql_query(query, self._data)[col_name].values

      return options

   @timer
   def _get_queue_info(self, df, current_time):

      cur = self._data.cursor()
      queue_info = {}
      for sender in df[CommDataColumns.SENDER_NAME].unique():
         try:
            comms = cur.execute(f'''
               SELECT DISTINCT {CommDataColumns.SENDERPART_NAME}
               FROM {COMM_DATA_TABLE}
               WHERE {CommDataColumns.SENDER_NAME} = '{sender}'
               AND {SharedColumns.EVENT_TYPE} IN ('MESSAGE_QUEUED', 'MESSAGE_TRANSMITTED')
               AND {SharedColumns.SIMULATION_TIME} <= {current_time}
               ''').fetchall()
            
            if len(comms) > 0:
               queue_info[sender] = {comm[0]: 0 for comm in comms}

            for comm in comms:
               queue_size = cur.execute(f'''
                  SELECT {CommDataColumns.QUEUE_SIZE} 
                  FROM {COMM_DATA_TABLE}
                  WHERE {CommDataColumns.SENDER_NAME} = '{sender}'
                  AND {CommDataColumns.SENDERPART_NAME} = '{comm[0]}'
                  AND {SharedColumns.EVENT_TYPE} IN ('MESSAGE_QUEUED', 'MESSAGE_TRANSMITTED')
                  AND {SharedColumns.SIMULATION_TIME} <= {current_time}
                  ORDER BY {SharedColumns.SIMULATION_TIME} DESC, {SharedColumns.EVENT_TYPE} DESC LIMIT 1
                  ''').fetchone()[0]

               if queue_size > 0:
                  queue_info[sender][comm] = queue_size

         except TypeError as e:
            pdb.set_trace()
      
      cur.close()
      return queue_info

   def _define_time_label_callback(self):

      @self._app.callback(
         Output(TIME_LABEL, "children"),
         Input(TIME_SLIDER, "value"),
         Input(TIME_RANGE_SLIDER, "value"),
         Input(RADIOS, 'value'),
         State(SWITCH_ONE_TIME_SLIDER, 'on')
      )
      def _write_time_label(single_time, value, radio_val, time_slider_switch):

         if radio_val:
            if time_slider_switch:
               return f"Current Time: {single_time}"
            else:
               start_time, end_time = value
               return f"Data Displayed Between Times: {start_time} and {end_time}"
         else:
            return "Plots not tied to time!"


   def _define_barplot_callback(self):

      @self._app.callback(
         Output(BAR_GRAPH, "figure"),
         Input(TIME_SLIDER, "value"),
         Input(TIME_RANGE_SLIDER, "value"),
         Input(SUBPLOT_CATEGORY, "value"),
         Input(BAR_GRAPH_CATEGORY, "value"),
         Input(BAR_STACK_CATEGORY, "value"),
         Input(DISPLAY_MEMORY, "data"),
         Input(RADIOS, 'value'),
         Input(SWITCH_ONE_TIME_SLIDER, "on"),
      )
      def update_barplots(
         single_time, time_value, subplot_category, 
         bar_graph_category, bar_stack_category,
         filter_data, radio_val, time_slider_switch):

         if radio_val:
            if time_slider_switch:
               frame = self._filter_comm_table(single_time)
            else:
               frame = self._filter_comm_table(time_value, range_slider=True)
         else:
            use_filter = len(self._filter_statements) > 0
            query = f'''
               SELECT *
               FROM {COMM_DATA_TABLE}
               {f"WHERE {' AND '.join(self._filter_statements)}" if use_filter else ""}
               '''
            frame = pd\
               .read_sql_query(
                  sql=query, 
                  con=self._data, 
                  index_col=SharedColumns.EVENT_ID)\
               .replace('nan', np.nan)\
               .astype(PANDAS_COMM_DATA_TYPES)

         if not frame.empty:
            return BarPlot.generate_barplots(frame, subplot_category, bar_graph_category, bar_stack_category)
         else:
            return go.Figure({"data": None, "layout": self._empty_plot})


   def _define_network_plot_callback(self):

      @self._app.callback(
         Output(self._network_plot.figure_name, "figure"),
         Input(TIME_SLIDER, "value"),
         Input(TIME_RANGE_SLIDER, "value"),
         Input(NETWORK_LAYOUT, "value"),
         Input(DISPLAY_MEMORY, "data"),
         Input(RADIOS, 'value'),
         Input(QUEUE_INFO_TOGGLE, 'value'),
         Input(SWITCH_ONE_TIME_SLIDER, 'on')
      )
      def update_network_plot(
         single_time, time_range_value, 
         network_layout, filter_data, 
         radio_val, queue_info_toggle,
         time_slider_switch):

         if radio_val:
            if time_slider_switch:
               comm_df = self._filter_comm_table(single_time)
            else: # time_slider_switch = OFF
               comm_df = self._filter_comm_table(time_range_value, range_slider=True)
         else: # radio_val = NO
            if ctx.triggered_id == TIME_SLIDER or ctx.triggered_id == TIME_RANGE_SLIDER:
               return no_update

            use_filter = len(self._filter_statements) > 0
            query = f'''
               SELECT *
               FROM {COMM_DATA_TABLE}
               {f"WHERE {' AND '.join(self._filter_statements)}" if use_filter else ""}
               '''
            comm_df = pd\
               .read_sql_query(
                  sql=query, 
                  con=self._data, 
                  index_col=SharedColumns.EVENT_ID)\
               .replace('nan', np.nan)\
               .astype(PANDAS_COMM_DATA_TYPES)

         comm_df = comm_df[comm_df[SharedColumns.EVENT_TYPE].isin(self._external_messages)]
         return self._network_plot.generate_network_figure(
            comm_df, 
            network_layout, 
            self._empty_plot, 
            self._get_queue_info(comm_df, single_time) if (radio_val and time_slider_switch and queue_info_toggle) else None)


   def _define_plot_select_callback(self):

      @self._app.callback(
         Output(BAR_GRAPH, "style"),
         Output(self._network_plot.figure_name, "style"),
         Output(BARPLOT_OPTIONS, "style"),
         Output(NETWORK_OPTIONS, "style"),
         Input(PLOT_OPTIONS, "value"),
         State(BAR_GRAPH, "style"),
         State(self._network_plot.figure_name, "style"),
         State(BARPLOT_OPTIONS, "style"),
         State(NETWORK_OPTIONS, "style")
      )
      def select_plot(
         plot_option, 
         bar_graph_style, network_plot_style,
         bar_option_style, network_option_style):

         if plot_option == "Bar Plot":
            bar_graph_style["display"] = "block"
            network_plot_style["display"] = "none"
            bar_option_style["display"] = "block"
            network_option_style["display"] = "none"

         elif plot_option == "Network Plot":
            bar_graph_style["display"] = "none"
            network_plot_style["display"] = "block"
            bar_option_style["display"] = "none"
            network_option_style["display"] = "block"

         return bar_graph_style, network_plot_style, bar_option_style, network_option_style
      
   def _define_single_time_button_callback(self):

      @self._app.callback(
         Output(TIME_SLIDER, 'value', allow_duplicate=True),
         Input(PREVIOUS_TIME_SINGLE, 'n_clicks'),
         Input(NEXT_TIME_SINGLE, 'n_clicks'),
         State(TIME_SLIDER, 'value'),
         prevent_initial_call=True
      )
      def shift_time(previous_time, next_time, current_time):

         if current_time is None:
            return self._timestamps[0]

         current_idx = np.where(self._timestamps == current_time)[0][0]

         if ctx.triggered_id == PREVIOUS_TIME_SINGLE:
            if current_idx != 0:
               return self._timestamps[current_idx-1]
            else:
               return self._timestamps[0]
         
         if ctx.triggered_id == NEXT_TIME_SINGLE:
            if current_idx != self._timestamps.shape[0] - 1:
               return self._timestamps[current_idx+1]
            else:
               return self._timestamps[-1]


   def _define_time_button_callback(self):

      @self._app.callback(
         Output(TIME_RANGE_SLIDER, 'value', allow_duplicate=True),
         Input(PREVIOUS_TIME_LEFT, 'n_clicks'),
         Input(NEXT_TIME_LEFT, 'n_clicks'),
         Input(PREVIOUS_TIME_RIGHT, 'n_clicks'),
         Input(NEXT_TIME_RIGHT, 'n_clicks'),
         State(TIME_RANGE_SLIDER, 'value'),
         prevent_initial_call=True
      )
      def shift_time(
         previous_time_left, next_time_left, 
         previous_time_right, next_time_right, 
         current_time):

         left_time, right_time = current_time
         left_idx = np.where(self._timestamps == left_time)[0][0]
         right_idx = np.where(self._timestamps == right_time)[0][0]

         if ctx.triggered_id == PREVIOUS_TIME_LEFT: 
            if left_idx != 0:
               return [self._timestamps[left_idx-1], right_time]
            else:
               return [self._timestamps[0], right_time]

         elif ctx.triggered_id == PREVIOUS_TIME_RIGHT:
            if right_idx > left_idx:
               if right_idx != 0:
                  return [left_time, self._timestamps[right_idx-1]]
               else:
                  return [left_time, self._timestamps[0]]
            else:
               return [left_time, right_time]

         if ctx.triggered_id == NEXT_TIME_LEFT:
            if left_idx < right_idx:
               if left_idx != self._timestamps.shape[0] - 1:
                  return [self._timestamps[left_idx+1], right_time]
               else:
                  return [self._timestamps[-1], right_time]
            else:
               return [left_time, right_time]
         
         elif ctx.triggered_id == NEXT_TIME_RIGHT:
            if right_idx != self._timestamps.shape[0] - 1:
               return [left_time, self._timestamps[right_idx+1]]
            else:
               return [left_time, self._timestamps[-1]]

   def _define_boolean_switch_callback(self):

      @self._app.callback(
         Output(TIME_SINGLE, 'style'), 
         Output(TIME_DOUBLE, 'style'),
         Input(SWITCH_ONE_TIME_SLIDER, 'on'),
         State(TIME_SINGLE, 'style'),
         State(TIME_DOUBLE, 'style'),
         prevent_initial_call=True
      )
      def toggle_switch(
         time_slider_switch, 
         time_single, time_double):

         if time_slider_switch:
            time_single["display"] = "block"
            time_double["display"] = "none"
         else:
            time_single["display"] = "none"
            time_double["display"] = "block"
         return [time_single, time_double]


   def _define_filter_callback(self):

      @self._app.callback(
         [Output(GLOBE_GRAPH, 'figure'),
         # Output('empty-dataframe-message', 'style'), Output('empty-dataframe-message', 'children'),
         Output(TIME_SLIDER, 'min'), Output(TIME_SLIDER, 'max'),
         Output(TIME_SLIDER, 'value'), Output(TIME_SLIDER, 'marks'),
         Output(TIME_RANGE_SLIDER, 'min'), Output(TIME_RANGE_SLIDER, 'max'),
         Output(TIME_RANGE_SLIDER, 'value'), Output(TIME_RANGE_SLIDER, 'marks')],
         Input(TIME_SLIDER, 'value'),
         Input(TIME_RANGE_SLIDER, 'value'),
         Input(SWITCH_ONE_TIME_SLIDER, 'on'),
         Input(DISPLAY_MEMORY, "data"),
         # State('empty-dataframe-message', 'style')
      )
      def filter_frame(single_time, value, time_slider_switch, filter_data):

         if time_slider_switch:
            current_data = self._get_current_data(single_time, time_slider_switch)
         else:
            current_data = self._get_current_data(value, time_slider_switch)

         external = current_data["comm"]["external"]
         internal = current_data["comm"]["internal"]

         update = []
         if not external.empty:
            transmission_plots, transmission_directions = GlobeComms.update_external_events(external)
            update.extend(transmission_directions)
            update.extend(transmission_plots)

         if not internal.empty:
            new_plot = GlobeComms.update_internal_events(internal)
            update.append(new_plot)

         self._globe_plot.set_camera_view(current_data)
         fig = self._globe_plot.build_earth_figure(update)

         if ctx.triggered_id != TIME_SLIDER and ctx.triggered_id != TIME_RANGE_SLIDER and len(self._timestamps) != 0:
            slider_marks = {}
            for val in self._timestamps:
               slider_marks[val] = '' 
            return [
               fig, 
               self._timestamps[0], 
               self._timestamps[-1], 
               self._timestamps[0],
               slider_marks,
               self._timestamps[0], 
               self._timestamps[-1], 
               [self._timestamps[0], 
                self._timestamps[-1] if len(self._timestamps) <= SLIDER_UPPER_LIMIT else self._timestamps[SLIDER_UPPER_LIMIT-1]],
               slider_marks]
         else:
            return [
               fig, 
               no_update, 
               no_update, 
               no_update, 
               no_update, 
               no_update, 
               no_update, 
               no_update, 
               no_update]

   def _define_cesium_filter_callback(self):

      @self._app.callback(
         [Output(CESIUM_EXTERNAL, 'data'), Output(CESIUM_INTERNAL, 'data'), 
          Output(CESIUM_CAMERA, 'data'),
         Output(TIME_SLIDER, 'min'), Output(TIME_SLIDER, 'max'),
         Output(TIME_SLIDER, 'value'), Output(TIME_SLIDER, 'marks'),
         Output(TIME_RANGE_SLIDER, 'min'), Output(TIME_RANGE_SLIDER, 'max'),
         Output(TIME_RANGE_SLIDER, 'value'), Output(TIME_RANGE_SLIDER, 'marks')],
         Input(TIME_SLIDER, 'value'),
         Input(TIME_RANGE_SLIDER, 'value'),
         Input(SWITCH_ONE_TIME_SLIDER, "on"),
         Input(DISPLAY_MEMORY, 'data')
      )
      def cesium_globe_callback(single_time, value, time_slider_switch, filter_data):

         if time_slider_switch:
            current_data = self._get_current_data(single_time, time_slider_switch)
         else:
            current_data = self._get_current_data(value, time_slider_switch)

         external = current_data["comm"]["external"]
         internal = current_data["comm"]["internal"]

         external_json = {}
         if not external.empty:
            group_idx = 1
            for transmission, group in external.groupby([
               CommDataColumns.SENDER_NAME, 
               CommDataColumns.SENDERPART_NAME, 
               CommDataColumns.RECEIVER_NAME, 
               CommDataColumns.RECEIVERPART_NAME]):

               sender_name, _, receiver_name, _ = transmission
               sender_location = np.array([
                  group[CommDataColumns.SENDERLOCATION_X].values[0], 
                  group[CommDataColumns.SENDERLOCATION_Y].values[0], 
                  group[CommDataColumns.SENDERLOCATION_Z].values[0]])

               receiver_location = np.array([
                  group[CommDataColumns.RECEIVERLOCATION_X].values[0], 
                  group[CommDataColumns.RECEIVERLOCATION_Y].values[0], 
                  group[CommDataColumns.RECEIVERLOCATION_Z].values[0]])
                              
               platform_range = group[CommDataColumns.SENDERTORCVR_RANGE].values[0]

               x, y, z = CesiumJSGlobe.get_line_points(sender_name, sender_location, receiver_name, receiver_location, platform_range)
               external_json[f"group_{group_idx}"] = {
                  "transmission": list(transmission), 
                  "info": group.to_dict(),
                  "line_points": {"x": x, "y": y, "z": z}}

               group_idx += 1

         internal_json = {}
         if not internal.empty:
            for sender, group in internal.groupby(CommDataColumns.SENDER_NAME):
               internal_json[sender] = group.to_dict()

         camera_view = CesiumJSGlobe.set_camera_view(internal, external)

         if ctx.triggered_id != TIME_SLIDER and ctx.triggered_id != TIME_RANGE_SLIDER and len(self._timestamps) != 0:
            slider_marks = {}
            for val in self._timestamps:
               slider_marks[val] = '' 
            return [
               json.dumps(external_json), 
               json.dumps(internal_json), 
               json.dumps(camera_view), 
               self._timestamps[0], 
               self._timestamps[-1], 
               self._timestamps[0],
               slider_marks,
               self._timestamps[0], 
               self._timestamps[-1], 
               [self._timestamps[0], 
               self._timestamps[-1] if len(self._timestamps) <= SLIDER_UPPER_LIMIT else self._timestamps[SLIDER_UPPER_LIMIT-1]],
               slider_marks]
         else:
            return [
               json.dumps(external_json), 
               json.dumps(internal_json), 
               json.dumps(camera_view), 
               no_update,
               no_update,
               no_update,
               no_update,
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

         self._comm_filter_options[SharedColumns.EVENT_TYPE] = evt_type
         self._comm_filter_options[CommDataColumns.MESSAGE_SERIALNUMBER] = msg_serial_number
         self._comm_filter_options[CommDataColumns.MESSAGE_ORIGINATOR] = msg_originator
         self._comm_filter_options[CommDataColumns.MESSAGE_TYPE] = msg_type
         self._comm_filter_options[CommDataColumns.SENDER_NAME] = sender_name
         self._comm_filter_options[CommDataColumns.SENDER_SIDE] = sender_side
         self._comm_filter_options[CommDataColumns.SENDER_TYPE] = sender_type
         self._comm_filter_options[CommDataColumns.SENDER_BASETYPE] = sender_basetype
         self._comm_filter_options[CommDataColumns.SENDERPART_NAME] = sender_part
         self._comm_filter_options[CommDataColumns.SENDERPART_TYPE] = sender_part_type
         self._comm_filter_options[CommDataColumns.SENDERPART_BASETYPE] = sender_part_basetype
         self._comm_filter_options[CommDataColumns.RECEIVER_NAME] = rcvr_name
         self._comm_filter_options[CommDataColumns.RECEIVER_SIDE] = rcvr_side
         self._comm_filter_options[CommDataColumns.RECEIVER_TYPE] = rcvr_type
         self._comm_filter_options[CommDataColumns.RECEIVER_BASETYPE] = rcvr_basetype
         self._comm_filter_options[CommDataColumns.RECEIVERPART_NAME] = rcvr_part
         self._comm_filter_options[CommDataColumns.RECEIVERPART_TYPE] = rcvr_part_type
         self._comm_filter_options[CommDataColumns.RECEIVERPART_BASETYPE] = rcvr_part_basetype

         self._filter_statements = [
            f'''{key} IN ('{"', '".join(map(str, vals))}')''' 
            for key, vals in self._comm_filter_options.items()
            if vals is not None and len(vals) != 0]

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
         for column in self._comm_filter_options:
            options.append(self._update_options(column, "COMM"))

         options.append(True)
         
         return options