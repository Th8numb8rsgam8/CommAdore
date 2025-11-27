from . import *
import dash_bootstrap_components as dbc
from dash import dcc, html, Dash


class DashLayout:

   def __init__(self, 
      data, 
      timestamps, 
      classification, 
      network_plot_name,
      cesium_config=None,
      use_cesium=False):

      self._data = data
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


   def initialize_barplot(self):

      barplot = dcc.Graph(
         id=BAR_GRAPH, 
         config={"scrollZoom": False}, 
         style={'height': '200vh'}
      )

      return barplot


   def initialize_barplot_options(self):

      subplot_options = [
         "ISODate", "Event_Type", "Message_SerialNumber", "Message_Originator",
         "Message_Type", "Message_Size", "Message_Priority", "Message_DataTag",
         "OldMessage_SerialNumber", "OldMessage_Originator", "OldMessage_Type",
         "OldMessage_Size", "OldMessage_Priority", "OldMessage_DataTag",
         "Sender_Name", "Sender_Type", "Sender_BaseType",
         "SenderPart_Name", "SenderPart_Type", "SenderPart_BaseType",
         "Receiver_Name", "Receiver_Type", "Receiver_BaseType",
         "ReceiverPart_Name", "ReceiverPart_Type", "ReceiverPart_BaseType",
         "CommInteraction_Succeeded", "CommInteraction_Failed",
         "CommInteraction_FailedStatus", "Queue_Size"]

      barplot_dropdowns = dbc.AccordionItem([
         self._create_dropdown("Subplot Category", SUBPLOT_CATEGORY, subplot_options, False, None, "Event_Type", False),
         self._create_dropdown("Bar Graph Category", BAR_GRAPH_CATEGORY, subplot_options, False, None, "Sender_Name", False),
         self._create_dropdown("Bar Stack Category", BAR_STACK_CATEGORY, subplot_options, False, None, "Receiver_Name", False)
      ], title="Bar Charts Options")

      return barplot_dropdowns


   def initialize_network_plot(self):

      network_plot = dcc.Graph(
         id=self._network_plot_name, 
         config={"scrollZoom": True}, 
         style={"height": "80vh"})

      return network_plot


   def initialize_network_options(self):

      network_options = ["Spring", "Circular", "Shell", "Spectral", "Random"]

      network_dropdowns = dbc.AccordionItem([
         self._create_dropdown("Network Layout", NETWORK_LAYOUT, network_options, False, None, "Spring", False),
      ], title="Network Options")

      return [network_dropdowns, self._create_button_group(QUEUE_INFO_TOGGLE, "Display Queue Info", is_option=True)]


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
               'border': '1px solid black'
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
               self._create_slider(),
               self._create_time_buttons()
            ], width=6),
            dbc.Col([
               self._create_dropdown("Plots", PLOT_OPTIONS, ["Bar Plot", "Network Plot"], False, False, "Bar Plot", False),
               self._create_plots_area(),
               self._create_time_label(),
               self._create_button_group(RADIOS, "Connect to Time Slider")
            ], width=6)
      ])

      return displayed_data


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
            "transform": "convertToHMS"
         })

      return slider


   def _create_time_buttons(self):

      buttons = html.Div(
         style={
            'textAlign': 'center',
            'paddingBottom': '20px'
         },
         children=[
            dbc.Button("Previous Time", id=PREVIOUS_TIME, color="primary"),
            dbc.Button("Next Time", id=NEXT_TIME, color="primary")
         ]
      )

      return buttons


   def _create_plots_area(self):

      bar_plots = dcc.Loading(
         children=[html.Div(
            id=PLOTS_AREA,
            style={
               'overflowY': 'scroll',
               'height': '80vh'
            },
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
            self._create_dropdown("Event Type", EVENT_TYPE, self._data["comm"]["Event_Type"].unique(), True, "All Events"),
            self._create_dropdown("Message Serial Number", MSG_SERIAL_NUMBER, self._data["comm"]["Message_SerialNumber"].unique(), True, "All Serial Numbers"),
            self._create_dropdown("Message Originator", MSG_ORIGINATOR, self._data["comm"]["Message_Originator"].unique(), True, "All Originators"),
            self._create_dropdown("Message Type", MSG_TYPE, self._data["comm"]["Message_Type"].unique(), True, "All Message Types"),
            self._create_dropdown("Sender", SENDER_NAME, self._data["comm"]["Sender_Name"].unique(), True, "All Senders"),
            self._create_dropdown("Sender Side", SENDER_SIDE, self._data["comm"]["Sender_Side"].unique(), True, "All Sides"),
            self._create_dropdown("Sender Type", SENDER_TYPE, self._data["comm"]["Sender_Type"].unique(), True, "All Sender Types"),
            self._create_dropdown("Sender BaseType", SENDER_BASETYPE, self._data["comm"]["Sender_BaseType"].unique(), True, "All Sender BaseTypes"),
            self._create_dropdown("Sender Part", SENDER_PART, self._data["comm"]["SenderPart_Name"].unique(), True, "All Sender Parts"),
            self._create_dropdown("Sender Part Type", SENDER_PART_TYPE, self._data["comm"]["SenderPart_Type"].unique(), True, "All Sender Part Types"),
            self._create_dropdown("Sender Part BaseType", SENDER_PART_BASETYPE, self._data["comm"]["SenderPart_BaseType"].unique(), True, "All Sender Part BaseTypes"),
            self._create_dropdown("Receiver", RECEIVER_NAME, self._data["comm"]["Receiver_Name"].unique(), True, "All Receivers"),
            self._create_dropdown("Receiver Side", RECEIVER_SIDE, self._data["comm"]["Receiver_Side"].unique(), True, "All Sides"),
            self._create_dropdown("Receiver Type", RECEIVER_TYPE, self._data["comm"]["Receiver_Type"].unique(), True, "All Receiver Types"),
            self._create_dropdown("Receiver BaseType", RECEIVER_BASETYPE, self._data["comm"]["Receiver_BaseType"].unique(), True, "All Receiver BaseTypes"),
            self._create_dropdown("Receiver Part", RECEIVER_PART, self._data["comm"]["ReceiverPart_Name"].unique(), True, "All Receiver Parts"),
            self._create_dropdown("Receiver Part Type", RECEIVER_PART_TYPE, self._data["comm"]["ReceiverPart_Type"].unique(), True, "All Receiver Part Types"),
            self._create_dropdown("Receiver Part BaseType", RECEIVER_PART_BASETYPE, self._data["comm"]["ReceiverPart_BaseType"].unique(), True, "All Receiver Part BaseTypes"),
            ], title="Comm Filter Options")],
            start_collapsed=True
         )

      return filter_options

   def _create_track_filter_options(self):

      filter_options = dbc.Accordion(
         children=[dbc.AccordionItem([
            self._create_dropdown("Owning Platform", OWNING_PLATFORM, self._data["track"]["Owning_Platform"].unique(), True, "All Platforms"),
            self._create_dropdown("Owning Platform Type", OWNING_PLATFORM_TYPE, self._data["track"]["Platform_Type"].unique(), True, "All Platform Types"),
            ], title="Track Filter Options")],
            start_collapsed=True
         )

      return filter_options


   def _create_plot_filters(self):

      subplot_filters = dbc.Accordion(id=PLOT_FILTERS, start_collapsed=True)

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