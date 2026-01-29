from . import *
from ..mission_execution import *
import pandas as pd
import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import dcc, html, Dash


class DashLayout:

   def __init__(self, 
      data, 
      timestamps, 
      classification, 
      network_plot_name,
      cesium_config=None,
      use_cesium=False):

      self._db_conn = data
      self._timestamps = timestamps
      self._classification = classification
      self._network_plot_name = network_plot_name
      self._cesium_config = cesium_config
      self._use_cesium = use_cesium

      self._app = Dash(
         title=APP_NAME,
         external_stylesheets=[
            '/static/styles.css',
            '/static/bootstrap.min.css'
         ]
      )

      self._set_dash_layout()


   def get_app(self):

      return self._app


   def _initialize_barplot(self):

      barplot = dcc.Graph(
         id=BAR_GRAPH, 
         config={"scrollZoom": False}, 
         style={
            'height': '200vh',
            'display': 'block'
         }
      )

      return barplot

   def _get_unique_values(self, col_name, table_name):
      values = pd.read_sql_query(
         f'SELECT DISTINCT {col_name} FROM {table_name}', 
         self._db_conn)[col_name].values
      return values

   def _initialize_barplot_options(self):

      subplot_options = [
         SharedColumns.ISO_DATE, 
         SharedColumns.EVENT_TYPE, 
         CommDataColumns.MESSAGE_SERIALNUMBER, 
         CommDataColumns.MESSAGE_ORIGINATOR,
         CommDataColumns.MESSAGE_TYPE, 
         CommDataColumns.MESSAGE_SIZE, 
         CommDataColumns.MESSAGE_PRIORITY, 
         CommDataColumns.MESSAGE_DATATAG,
         CommDataColumns.OLDMESSAGE_SERIALNUMBER, 
         CommDataColumns.OLDMESSAGE_ORIGINATOR, 
         CommDataColumns.OLDMESSAGE_TYPE,
         CommDataColumns.OLDMESSAGE_SIZE, 
         CommDataColumns.OLDMESSAGE_PRIORITY, 
         CommDataColumns.OLDMESSAGE_DATATAG,
         CommDataColumns.SENDER_NAME, 
         CommDataColumns.SENDER_TYPE, 
         CommDataColumns.SENDER_BASETYPE,
         CommDataColumns.SENDERPART_NAME, 
         CommDataColumns.SENDERPART_TYPE, 
         CommDataColumns.SENDERPART_BASETYPE,
         CommDataColumns.RECEIVER_NAME, 
         CommDataColumns.RECEIVER_TYPE, 
         CommDataColumns.RECEIVER_BASETYPE,
         CommDataColumns.RECEIVERPART_NAME, 
         CommDataColumns.RECEIVERPART_TYPE, 
         CommDataColumns.RECEIVERPART_BASETYPE,
         CommDataColumns.COMMINTERACTION_SUCCEEDED, 
         CommDataColumns.COMMINTERACTION_FAILED,
         CommDataColumns.COMMINTERACTION_FAILEDSTATUS, 
         CommDataColumns.QUEUE_SIZE
      ]

      barplot_dropdowns = dbc.AccordionItem([
         self._create_dropdown("Subplot Category", SUBPLOT_CATEGORY, subplot_options, False, None, SharedColumns.EVENT_TYPE, False),
         self._create_dropdown("Bar Graph Category", BAR_GRAPH_CATEGORY, subplot_options, False, None, CommDataColumns.SENDER_NAME, False),
         self._create_dropdown("Bar Stack Category", BAR_STACK_CATEGORY, subplot_options, False, None, CommDataColumns.RECEIVER_NAME, False)
      ], title="Bar Charts Options")

      barplot_options = dbc.Accordion(
         id=BARPLOT_OPTIONS,
         style={
            'display': 'block'
         },
         children=[barplot_dropdowns],
         start_collapsed=True
      )

      return barplot_options


   def _initialize_network_plot(self):

      network_plot = dcc.Graph(
         id=self._network_plot_name, 
         config={"scrollZoom": True}, 
         style={
            'height': '80vh',
            'display': 'none'
         }
      )

      return network_plot


   def _initialize_network_options(self):

      network_options = ["Spring", "Circular", "Shell", "Spectral", "Random"]

      network_dropdowns = dbc.AccordionItem([
         self._create_dropdown("Network Layout", NETWORK_LAYOUT, network_options, False, None, "Spring", False),
      ], title="Network Options")

      network_options = html.Div(
         id=NETWORK_OPTIONS,
         style={
            'display': 'none'
         },
         children=[
            dbc.Accordion(
               children=[network_dropdowns],
               start_collapsed=True
            ),
            self._create_button_group(QUEUE_INFO_TOGGLE, "Display Queue Info", is_option=True)
         ]
      )

      return network_options


   def _set_dash_layout(self):
         
      self._app.layout = dcc.Loading(
         children=[
            html.Div(
               id=MAIN_DISPLAY,
               children=[
                  self._create_classification_markings("top"),
                  self._create_dataframe_message(),
                  self._create_displayed_data_row(),
                  self._create_options_row(),
                  self._create_classification_markings("bottom"),
               ]
            ),
            dcc.Store(id=FILTER_MEMORY),
            dcc.Store(id=DISPLAY_MEMORY),
            *self._add_cesium_elements()
         ],
         target_components={MAIN_DISPLAY: "children"},
      )

   def _add_cesium_elements(self):

      elements = [
         dcc.Store(id=CESIUM_VIEWER), 
         dcc.Store(id=CESIUM_CONFIG, data=self._cesium_config),
         dcc.Store(id=CESIUM_CAMERA),
         dcc.Store(id=CESIUM_EXTERNAL),
         dcc.Store(id=CESIUM_INTERNAL),
         dcc.Store(id=CESIUM_TRACKS),
         html.Div(
            id="tooltip",
            style={
               'position': 'absolute',
               'display': 'none',
               'background': 'white',
               'padding': '5px',
               'border': '1px solid black',
               'overflow-y': 'scroll',
               'height': '200px'
            }
         )
      ]

      return elements if self._use_cesium else []


   def _create_classification_markings(self, pos):

      markings = dbc.Row(
         id=f"{pos}-classification",
         style={
            'position': 'relative',
            'textAlign': 'center',
            'color': 'crimson',
            'fontSize': 'x-large',
            'fontWeight': 'bold',
            'zIndex': '5'
         },
         children=[
            dbc.Col(html.Label(self._classification), width=12)
         ]
      )

      return markings


   def _create_displayed_data_row(self):

      displayed_data = dbc.Row(
         id=DISPLAYED_DATA,
         style={
            'display': 'flex',
            'zIndex': '1'
         },
         children=[
            dbc.Col([
               self._create_globe_visual(),
               *self._create_slider_controls(),
               self._create_boolean_switch()
            ], width=6),
            dbc.Col([
               self._create_dropdown("Plots", PLOT_OPTIONS, ["Bar Plot", "Network Plot"], False, False, "Bar Plot", False),
               self._create_plots_area(),
               self._create_time_label(),
               self._create_button_group(RADIOS, "Connect to Time Slider")
            ], width=6)
      ])

      return displayed_data


   def _create_slider_controls(self):

      slider_controls = [
         html.Div(
            id=TIME_SINGLE,
            style={
               'display': 'none'
            },
            children=[
               self._create_slider(),
               self._create_time_buttons("Time Buttons", "center", 20),
            ]
         ),
         html.Div(
            id=TIME_DOUBLE,
            style={
               'display': 'block'
            },
            children=[
               self._create_range_slider(),
               html.Div(
                  id=TIME_BUTTON_GROUP,
                  children=[
                     self._create_time_buttons("Left Handle", "left", 40),
                     self._create_time_buttons("Right Handle", "right", 40)
                  ]
               )
            ]
         ),
      ]

      return slider_controls

   def _create_options_row(self):

      options_row = dbc.Row(
         id=OPTIONS_ROW,
         style={
            'position': 'relative',
            'textAlign': 'center',
            'zIndex': '5'
         },
         children=[
            dbc.Col([self._create_comm_filter_options(), self._create_track_filter_options()], width=6),
            dbc.Col(self._create_plot_filters(), width=6),
         ]
      )

      return options_row


   def _create_dataframe_message(self):

      df_message = html.Div(
         "ISR-AFSIM Works",
         id="empty-dataframe-message",
         style={
            'position': 'fixed',
            'left': '0',
            'height': '100%',
            'width': '100%',
            'textAlign': 'center',
            'paddingTop': '40vh',
            'fontSize': 'xxx-large',
            'fontWeight': 'bold',
            'opacity': '0.5',
            'backgroundColor': 'unset',
            'zIndex': '-1'
         }
      )

      return df_message


   def _create_globe_visual(self):

      if self._use_cesium:
         return html.Div(id=GLOBE_GRAPH, style={'height': '80vh'})
      else:
         return dcc.Graph(
         id=GLOBE_GRAPH, 
         config={"scrollZoom": True}, 
         style={'height': '80vh'})

   def _create_slider(self):

      slider_marks = {}
      for val in self._timestamps:
         slider_marks[val] = '' 

      slider = dcc.Slider(
         id=TIME_SLIDER,
         min=self._timestamps[0], 
         max=self._timestamps[-1],
         step=None,
         marks=eval(str(slider_marks)),
         value=self._timestamps[0], 
         dots=False,
         updatemode="mouseup",
         tooltip={
            "placement": "top", 
            "always_visible": True,
            "transform": None 
         })

      return slider

   def _create_range_slider(self):

      slider_marks = {}
      for val in self._timestamps:
         slider_marks[val] = '' 

      slider = dcc.RangeSlider(
         id=TIME_RANGE_SLIDER,
         min=self._timestamps[0], 
         max=self._timestamps[-1],
         step=None,
         marks=eval(str(slider_marks)),
         value=[
            self._timestamps[0], 
            self._timestamps[-1] if len(self._timestamps) <= SLIDER_UPPER_LIMIT else self._timestamps[SLIDER_UPPER_LIMIT-1]],
         dots=False,
         updatemode="mouseup",
         allowCross=False,
         tooltip={
            "placement": "top", 
            "always_visible": True,
            "transform": None 
         })

      return slider


   def _create_time_buttons(self, button_label, slider_side, button_width):

      prev_id = PREVIOUS_TIME_LEFT if slider_side == "left" else PREVIOUS_TIME_RIGHT if slider_side == "right" else PREVIOUS_TIME_SINGLE
      next_id = NEXT_TIME_LEFT if slider_side == "left" else NEXT_TIME_RIGHT if slider_side == "right" else NEXT_TIME_SINGLE

      buttons = html.Div(
         style={
            'textAlign': 'center',
            'paddingBottom': '20px'
         },
         children=[
            dbc.Row(html.Label(button_label)),
            dbc.Row(
               html.Div(
                  children=[
                     dbc.Button(
                        "Previous Time", 
                        id=f"{prev_id}", 
                        outline=True, 
                        color="secondary",
                        style={'width': f'{button_width}%'}),
                     dbc.Button(
                        "Next Time", 
                        id=f"{next_id}", 
                        outline=True, 
                        color="secondary",
                        style={'width': f'{button_width}%'})
                  ]
               )
            )
         ]
      )

      return buttons

   def _create_boolean_switch(self):

      switch = html.Div(
         className="switch-row",
         children=[
            # daq.BooleanSwitch(
            #    id=SWITCH_ISO_DATE,
            #    on=False,
            #    persistence=False,
            #    persisted_props=None,
            #    label={
            #       'label': "ISO Date Format"
            #    }
            # ),
            daq.BooleanSwitch(
               id=SWITCH_ONE_TIME_SLIDER,
               on=False,
               persistence=False,
               persisted_props=None,
               label={
                  'label': "Single Time Slider"
               }
            )
         ]
      )

      return switch


   def _create_plots_area(self):

      bar_plots = dcc.Loading(
         children=[html.Div(
            id=PLOTS_AREA,
            style={
               'overflowY': 'scroll',
               'height': '80vh'
            },
            children=[
               self._initialize_barplot(),
               self._initialize_network_plot()
            ]
         )],
         target_components={
            BAR_GRAPH: "figure",
            self._network_plot_name: "figure"},
         type="graph"
      )
         
      return bar_plots


   def _create_time_label(self):

      time_label = html.Div(
         id=TIME_LABEL,
         style={
            'textAlign': 'center',
            'fontWeight': 'bold',
            'paddingTop': '20px'
         }
      )

      return time_label


   def _create_button_group(self, ID, label_text, is_option=False):

      button_group = html.Div(
         children=[
            dbc.Row(html.Label(
               label_text, 
               className="radio-label" if is_option else None)),
            dbc.Row(
               children=[
                  html.Div(
                     dbc.RadioItems(
                     id=ID,
                     className="btn-group",
                     inputClassName="btn-check",
                     labelClassName="btn btn-outline-primary",
                     labelCheckedClassName="active",
                     options=[
                        {"label": "YES", "value": 1},
                        {"label": "NO", "value": 0}
                     ],
                     value=1
                  )
               )]
            )
         ],
         className=f"radio-group {'radio-option' if is_option else ''}"
      )

      return button_group


   def _create_comm_filter_options(self):

      filter_options = dbc.Accordion(
         children=[dbc.AccordionItem([
            self._create_dropdown("Event Type", EVENT_TYPE, self._get_unique_values(SharedColumns.EVENT_TYPE, COMM_DATA_TABLE), True, "All Events"),
            self._create_dropdown("Message Serial Number", MSG_SERIAL_NUMBER, self._get_unique_values(CommDataColumns.MESSAGE_SERIALNUMBER, COMM_DATA_TABLE), True, "All Serial Numbers"),
            self._create_dropdown("Message Originator", MSG_ORIGINATOR, self._get_unique_values(CommDataColumns.MESSAGE_ORIGINATOR, COMM_DATA_TABLE), True, "All Originators"),
            self._create_dropdown("Message Type", MSG_TYPE, self._get_unique_values(CommDataColumns.MESSAGE_TYPE, COMM_DATA_TABLE), True, "All Message Types"),
            self._create_dropdown("Sender", SENDER_NAME, self._get_unique_values(CommDataColumns.SENDER_NAME, COMM_DATA_TABLE), True, "All Senders"),
            self._create_dropdown("Sender Side", SENDER_SIDE, self._get_unique_values(CommDataColumns.SENDER_SIDE, COMM_DATA_TABLE), True, "All Sides"),
            self._create_dropdown("Sender Type", SENDER_TYPE, self._get_unique_values(CommDataColumns.SENDER_TYPE, COMM_DATA_TABLE), True, "All Sender Types"),
            self._create_dropdown("Sender BaseType", SENDER_BASETYPE, self._get_unique_values(CommDataColumns.SENDER_BASETYPE, COMM_DATA_TABLE), True, "All Sender BaseTypes"),
            self._create_dropdown("Sender Part", SENDER_PART, self._get_unique_values(CommDataColumns.SENDERPART_NAME, COMM_DATA_TABLE), True, "All Sender Parts"),
            self._create_dropdown("Sender Part Type", SENDER_PART_TYPE, self._get_unique_values(CommDataColumns.SENDERPART_TYPE, COMM_DATA_TABLE), True, "All Sender Part Types"),
            self._create_dropdown("Sender Part BaseType", SENDER_PART_BASETYPE, self._get_unique_values(CommDataColumns.SENDERPART_BASETYPE, COMM_DATA_TABLE), True, "All Sender Part BaseTypes"),
            self._create_dropdown("Receiver", RECEIVER_NAME, self._get_unique_values(CommDataColumns.RECEIVER_NAME, COMM_DATA_TABLE), True, "All Receivers"),
            self._create_dropdown("Receiver Side", RECEIVER_SIDE, self._get_unique_values(CommDataColumns.RECEIVER_SIDE, COMM_DATA_TABLE), True, "All Sides"),
            self._create_dropdown("Receiver Type", RECEIVER_TYPE, self._get_unique_values(CommDataColumns.RECEIVER_TYPE, COMM_DATA_TABLE), True, "All Receiver Types"),
            self._create_dropdown("Receiver BaseType", RECEIVER_BASETYPE, self._get_unique_values(CommDataColumns.RECEIVER_BASETYPE, COMM_DATA_TABLE), True, "All Receiver BaseTypes"),
            self._create_dropdown("Receiver Part", RECEIVER_PART, self._get_unique_values(CommDataColumns.RECEIVERPART_NAME, COMM_DATA_TABLE), True, "All Receiver Parts"),
            self._create_dropdown("Receiver Part Type", RECEIVER_PART_TYPE, self._get_unique_values(CommDataColumns.RECEIVERPART_TYPE, COMM_DATA_TABLE), True, "All Receiver Part Types"),
            self._create_dropdown("Receiver Part BaseType", RECEIVER_PART_BASETYPE, self._get_unique_values(CommDataColumns.RECEIVERPART_BASETYPE, COMM_DATA_TABLE), True, "All Receiver Part BaseTypes"),
            ], title="Comm Filter Options")],
            start_collapsed=True
         )

      return filter_options

   def _create_track_filter_options(self):

      filter_options = dbc.Accordion(
         children=[dbc.AccordionItem([
            self._create_dropdown("Owning Platform", OWNING_PLATFORM, self._get_unique_values(TrackDataColumns.OWNING_PLATFORM, TRACK_DATA_TABLE), True, "All Platforms"),
            self._create_dropdown("Owning Platform Type", OWNING_PLATFORM_TYPE, self._get_unique_values(TrackDataColumns.PLATFORM_TYPE, TRACK_DATA_TABLE), True, "All Platform Types"),
            ], title="Track Filter Options")],
            start_collapsed=True
         )

      return filter_options


   def _create_plot_filters(self):

      subplot_filters = html.Div(
         id=PLOT_FILTERS,
         children=[
            self._initialize_barplot_options(),
            self._initialize_network_options()
         ]
      )

      return subplot_filters 

   
   def _create_dropdown(self, col_name, dropdown_id, options, multi, placeholder=None, value=None, clearable=True):

      dropdown = html.Div(
         className='labeled-div',
         children=[
            html.Label(col_name),
            dcc.Dropdown(
               id=dropdown_id, 
               options=options,
               placeholder=placeholder,
               value=value,
               multi=multi,
               clearable=clearable)
         ]
      )

      return dropdown