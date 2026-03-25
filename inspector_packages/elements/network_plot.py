import sys
import networkx as nx
from inspector_packages import *
from utils import cli_output
from ..mission_execution import *


class NetworkPlot:

   def __init__(self):

      self._figure_name = "network-graph"

      self._edge_width = [
         {"range": [1, 10], "width": 0.5},
         {"range": [10, 20], "width": 1},
         {"range": [20, 30], "width": 1.5},
         {"range": [30, 40], "width": 2},
         {"range": [40, 50], "width": 2.5},
         {"range": [50, 60], "width": 3},
         {"range": [60, 70], "width": 3.5},
         {"range": [70, 80], "width": 4},
         {"range": [80, 90], "width": 4.5},
         {"range": [90, sys.maxsize], "width": 5},
      ]

      self._q_horizontal_spacing = 0.01
      self._q_vertical_spacing = 0.02
      self._q_item_width = 0.06
      self._q_item_height = 0.03


   @property
   def figure_name(self):

      return self._figure_name


   def generate_network_figure(self, comm_df, track_df, platform_df, network_layout, empty_plot, queue_info):

      node_positions, comm_edges, track_edges = self._get_network_layout(comm_df, track_df, network_layout)

      node_x, node_y, node_text, nodes_visited = {}, {}, {}, []
      nodes_traces, edge_traces, directions, queue_items = [], [], [], []
      one_way_transmissions, two_way_transmissions = [], []
      for transmission, group in comm_df.groupby([CommDataColumns.SENDER_NAME, CommDataColumns.RECEIVER_NAME]):

         sender, receiver = transmission[0], transmission[1]
         sender_type = group[CommDataColumns.SENDER_TYPE].iloc[0]
         receiver_type = group[CommDataColumns.RECEIVER_TYPE].iloc[0]

         sender_track_info = track_df[track_df[TrackDataColumns.OWNING_PLATFORM] == sender].tail(1) if track_df is not None else None
         rcvr_track_info = track_df[track_df[TrackDataColumns.OWNING_PLATFORM] == receiver].tail(1) if track_df is not None else None

         self._set_node_info(
            node_x, node_y, 
            node_text, node_positions, 
            nodes_visited, 
            sender, sender_type, sender_track_info)

         self._set_node_info(
            node_x, node_y, 
            node_text, node_positions, 
            nodes_visited, 
            receiver, receiver_type, rcvr_track_info)

         two_way = comm_df[(comm_df[CommDataColumns.SENDER_NAME] == receiver) & (comm_df[CommDataColumns.RECEIVER_NAME] == sender)]
         if not two_way.empty:
            if (sender, receiver) not in two_way_transmissions and (receiver, sender) not in two_way_transmissions:
               two_way_transmissions.append((sender, receiver))
            continue

         edge_width = self._get_edge_width(group.shape[0])
         arrow_text = self._get_arrow_text(group)

         edge_traces.append(self._add_edge(node_positions[sender], node_positions[receiver], edge_width, "comm"))
         directions.append(self._add_direction(node_positions[sender], node_positions[receiver], [arrow_text, arrow_text], "comm"))
         one_way_transmissions.append((sender, receiver))

      two_way_pts = self._handle_two_way_transmissions(comm_df, node_positions, two_way_transmissions, edge_traces, directions)

      two_way_tracks = []
      for track_pair in track_edges:
         contributor, owning_platform = track_pair
         two_way_track = (owning_platform, contributor) in track_edges
         if two_way_track:
            rcvr_info = track_df[track_df[TrackDataColumns.OWNING_PLATFORM] == owning_platform].tail(1)
            rcvr_type = rcvr_info[TrackDataColumns.PLATFORM_TYPE].iloc[0]
            self._set_node_info(
               node_x, node_y, 
               node_text, node_positions, 
               nodes_visited, 
               owning_platform, rcvr_type, rcvr_info)
            two_way_tracks.append(track_pair)
            continue

         one_way_comm = False
         for sender, receiver in one_way_transmissions:
            if sender in track_pair and receiver in track_pair:
               one_way_comm = True
               break

         if one_way_comm: # there is already a comm edge between nodes
            pos1 = node_positions[contributor]
            pos2 = node_positions[owning_platform]
            center, _ = self._find_normal_vectors(pos1, pos2, scale=2)
            contributor_to_rcvr = self._find_points_on_curve(pos1, pos2, center)
            two_way_pts.extend(contributor_to_rcvr)

            for i in range(len(contributor_to_rcvr)-1):
               edge_traces.append(self._add_edge(contributor_to_rcvr[i], contributor_to_rcvr[i+1], 3, "track"))
               directions.append(self._add_direction(contributor_to_rcvr[i], contributor_to_rcvr[i+1], ["TRACK INFO" + "<extra></extra>"] * 2, "track"))
            edge_traces.append(self._add_edge(contributor_to_rcvr[-1], pos2, 3, "track"))
         else: # two-way comm or no comm edges

            try:
               contributor_info = platform_df.loc[contributor]
               rcvr_info = track_df[track_df[TrackDataColumns.OWNING_PLATFORM] == owning_platform].tail(1)
               contributor_type = contributor_info[TrackDataColumns.PLATFORM_TYPE]
               rcvr_type = rcvr_info[TrackDataColumns.PLATFORM_TYPE].iloc[0]

               self._set_node_info(
                  node_x, node_y, 
                  node_text, node_positions, 
                  nodes_visited, 
                  contributor, contributor_type, None)

               self._set_node_info(
                  node_x, node_y, 
                  node_text, node_positions, 
                  nodes_visited, 
                  owning_platform, rcvr_type, rcvr_info)

               edge_traces.append(self._add_edge(node_positions[contributor], node_positions[owning_platform], 3, "track"))
               directions.append(self._add_direction(node_positions[contributor], node_positions[owning_platform], ["TRACK INFO" + "<extra></extra>"] * 2, "track"))

            except KeyError as e:
               cli_output.WARNING(f"{self.__class__.__name__}: {contributor} does not exist at time {platform_df[SharedColumns.ISO_DATE].iloc[0]}")

      two_way_track_pts = self._handle_two_way_tracks(track_df, node_positions, two_way_tracks, edge_traces, directions)

      for platform_type in node_x:
         nodes_traces.append(self._add_node(
            node_x[platform_type], 
            node_y[platform_type], 
            platform_type, 
            node_text[platform_type]))

      if queue_info is not None:
         self._add_queues(queue_info, node_positions, two_way_pts, queue_items)

      fig =  go.Figure({"data": nodes_traces + edge_traces + directions + queue_items, "layout": empty_plot})

      return fig
         

   def _get_network_layout(self, comm_df, track_df, network_layout):

      transmissions = comm_df[[CommDataColumns.SENDER_NAME, CommDataColumns.RECEIVER_NAME]].drop_duplicates()
      comm_edges = [(row[CommDataColumns.SENDER_NAME], row[CommDataColumns.RECEIVER_NAME]) for _, row in transmissions.iterrows()]

      track_edges = self._get_track_edges(track_df) if track_df is not None else []

      G = nx.Graph()
      G.add_edges_from(comm_edges + track_edges)

      if network_layout == "Spring":
         node_positions = nx.spring_layout(G)
      elif network_layout == "Circular":
         node_positions = nx.circular_layout(G)
      elif network_layout == "Shell":
         node_positions = nx.shell_layout(G)
      elif network_layout == "Spectral":
         node_positions = nx.spectral_layout(G)
      elif network_layout == "Random":
         node_positions = nx.random_layout(G)

      return node_positions, comm_edges, track_edges


   def _get_edge_width(self, num):

      edge_width = 0.25 
      for rng_step in self._edge_width:
         min_rng, max_rng = rng_step["range"]
         if min_rng < num <= max_rng:
            edge_width = rng_step["width"]
            break

      return edge_width


   def _get_arrow_text(self, df):

      msg_type_counts = df[CommDataColumns.MESSAGE_TYPE].value_counts().to_dict()
      arrow_text = f'{df[CommDataColumns.SENDER_NAME].iloc[0]} >> {df[CommDataColumns.RECEIVER_NAME].iloc[0]}<br>'
      for msg_type, count in msg_type_counts.items():
         arrow_text += f'{msg_type}: {count}<br>'
      arrow_text += '<extra></extra>'

      return arrow_text


   def _add_edge(self, start, end, edge_width, edge_type):

      edge = {
         "type": "scatter",
         "name": f"{edge_type}_edge",
         "x": [start[0], end[0]],
         "y": [start[1], end[1]],
         "mode": "lines",
         "hoverinfo": "none",
         "zorder": 1,
         "line": 
         {
            "width": edge_width,
            "dash": "solid" if edge_type == "comm" else "dot",
            "color": "black" if edge_type == "comm" else "#CD5C5C"
         },
         "showlegend": False
      }

      return edge

   
   def _add_direction(self, start, end, text, edge_type):

      arrow_start = start + 0.25 * (end - start)
      arrow_end = start + 0.75 * (end - start)

      direction = {
         "type": "scatter",
         "name": f"{edge_type}_edge",
         "x": [arrow_start[0], arrow_end[0]], 
         "y": [arrow_start[1], arrow_end[1]],
         "mode": "markers",
         "zorder": 1,
         "customdata": text,
         "hovertemplate":'%{customdata}',
         "marker":
         {
            "size": 15,
            "color": "black" if edge_type == "comm" else "#CD5C5C",
            "symbol": "arrow-up",
            "angleref": "previous"
         },
         "showlegend": False
      }

      return direction


   def _add_node(self, x, y, node_type, text):

      node = {
         "type": "scatter",
         "name": node_type,
         "x": x,
         "y": y,
         "mode": "markers",
         "zorder": 2,
         "customdata": text,
         "hovertemplate":'%{customdata}',
         "marker":
         {
            "size": 20,
         },
      }

      return node

   
   def _set_node_info(self, node_x, node_y, node_text, node_positions, nodes_visited, node_name, node_type, track_info):

      if node_name not in nodes_visited:
         if node_type not in node_x:
            node_x[node_type] = []
            node_y[node_type] = []
            node_text[node_type] = []

         pos = node_positions[node_name]
         node_x[node_type].append(pos[0])
         node_y[node_type].append(pos[1])
         txt = f"{node_name}<br>"
         if track_info is not None and not track_info.empty:
            track_count = track_info[TrackDataColumns.TRACK_LIST_COUNT].iloc[0]
            txt += f"Track Count: {track_count}<br>"
         txt += "<extra></extra>"
         node_text[node_type].append(txt)
         nodes_visited.append(node_name)


   def _handle_two_way_transmissions(self, frame, node_positions, two_way_transmissions, edge_traces, directions):

      two_way_pts = []
      for sender, receiver in two_way_transmissions:

         way1 = frame[(frame[CommDataColumns.SENDER_NAME] == sender) & (frame[CommDataColumns.RECEIVER_NAME] == receiver)]
         way2 = frame[(frame[CommDataColumns.SENDER_NAME] == receiver) & (frame[CommDataColumns.RECEIVER_NAME] == sender)]
         edge_width1 = self._get_edge_width(way1.shape[0])
         arrow_text1 = self._get_arrow_text(way1)
         edge_width2 = self._get_edge_width(way2.shape[0])
         arrow_text2 = self._get_arrow_text(way2)

         pos1 = node_positions[sender]
         pos2 = node_positions[receiver]
         center1, center2 = self._find_normal_vectors(pos1, pos2)
         sender_to_rcvr = self._find_points_on_curve(pos1, pos2, center1)
         rcvr_to_sender = self._find_points_on_curve(pos2, pos1, center2)
         two_way_pts.extend(sender_to_rcvr)
         two_way_pts.extend(rcvr_to_sender)

         for i in range(len(sender_to_rcvr)-1):
            edge_traces.append(self._add_edge(sender_to_rcvr[i], sender_to_rcvr[i+1], edge_width1, "comm"))
            directions.append(self._add_direction(sender_to_rcvr[i], sender_to_rcvr[i+1], [arrow_text1, arrow_text1], "comm"))
         edge_traces.append(self._add_edge(sender_to_rcvr[-1], pos2, edge_width1, "comm"))

         for i in range(len(rcvr_to_sender)-1):
            edge_traces.append(self._add_edge(rcvr_to_sender[i], rcvr_to_sender[i+1], edge_width2, "comm"))
            directions.append(self._add_direction(rcvr_to_sender[i], rcvr_to_sender[i+1], [arrow_text2, arrow_text2], "comm"))
         edge_traces.append(self._add_edge(rcvr_to_sender[-1], pos1, edge_width2, "comm"))

      return two_way_pts


   def _handle_two_way_tracks(self, frame, node_positions, two_way_tracks, edge_traces, directions):

      if len(two_way_tracks) >= 1:
         cli_output.INFO(f"{self.__class__.__name__}: NUMBER OF TWO WAY TRACKS {len(two_way_tracks)}")

      two_way_pts = []
      for contributor, owning_platform in two_way_tracks:

         if contributor != owning_platform:
            pos1 = node_positions[contributor]
            pos2 = node_positions[owning_platform]
            center1, center2 = self._find_normal_vectors(pos1, pos2, scale=2)
            sender_to_rcvr = self._find_points_on_curve(pos1, pos2, center1)
            rcvr_to_sender = self._find_points_on_curve(pos2, pos1, center2)
            two_way_pts.extend(sender_to_rcvr)
            two_way_pts.extend(rcvr_to_sender)

            for i in range(len(sender_to_rcvr)-1):
               edge_traces.append(self._add_edge(sender_to_rcvr[i], sender_to_rcvr[i+1], 3, "track"))
               directions.append(self._add_direction(sender_to_rcvr[i], sender_to_rcvr[i+1], ["TRACK INFO" + "<extra></extra>"] * 2, "track"))

            edge_traces.append(self._add_edge(sender_to_rcvr[-1], pos2, 3, "track"))

            for i in range(len(rcvr_to_sender)-1):
               edge_traces.append(self._add_edge(rcvr_to_sender[i], rcvr_to_sender[i+1], 3, "track"))
               directions.append(self._add_direction(rcvr_to_sender[i], rcvr_to_sender[i+1], ["TRACK INFO" + "<extra></extra>"] * 2, "track"))
            edge_traces.append(self._add_edge(rcvr_to_sender[-1], pos1, 3, "track"))

         else:
            cli_output.INFO(f"{self.__class__.__name__}: {contributor} contributes track to its own list.")

      return two_way_pts


   def _add_queues(self, queue_info, node_positions, two_way_pts, queue_items):

      min_x, max_x, min_y, max_y = self._get_graph_limits(node_positions, two_way_pts)
      for sender, comms in queue_info.items():
         queue_horizontal_spacing = self._q_horizontal_spacing * (max_x - min_x)
         queue_vertical_spacing = self._q_vertical_spacing * (max_y - min_y)
         queue_item_width = self._q_item_width * (max_x - min_x)
         queue_item_height = self._q_item_height * (max_y - min_y)
         queues_x_left, queues_x_right = [], []
         num_queues = len(comms)
         even_queues = num_queues % 2 == 0
         first_split = queue_horizontal_spacing if even_queues else queue_item_width
         x0, y0 = node_positions[sender]
         queues_x_left.append(x0 - first_split / 2) 
         queues_x_right.append(x0 + first_split / 2)
         for i in range(num_queues-1):
            use_width = (i % 2 == 0) if even_queues else (i % 2 == 1)
            shift = queue_item_width if use_width else queue_horizontal_spacing
            queues_x_left.append(queues_x_left[-1] - shift)
            queues_x_right.append(queues_x_right[-1] + shift)

         queues_x = sorted(queues_x_left) + queues_x_right
         for i, comm in enumerate(comms):
            queue_x0, queue_x1 = queues_x[i*2:(i+1)*2]
            update_shift = y0 
            queue_size = comms[comm]
            for item_num in range(queue_size):
               update_shift += queue_vertical_spacing
               queue_y0 = update_shift
               update_shift += queue_item_height
               queue_y1 = update_shift

               queue_item = {
                  "type": "scatter",
                  "name": "queue_item",
                  "x": [queue_x0, queue_x1, queue_x1, queue_x0, queue_x0],
                  "y": [queue_y0, queue_y0, queue_y1, queue_y1, queue_y0],
                  "mode": "lines",
                  "fill": "toself",
                  "fillcolor": "rgba(255,140,0,0.4)",
                  "zorder": 1,
                  "hoverinfo": "none",
                  "line": 
                  {
                     "width": 1,
                     "color": "black"
                  },
                  "showlegend": False
               }

               hover_info = {
                  "type": "scatter",
                  "name": "queue_item",
                  "x": [queue_x0 + 0.5 * (queue_x1 - queue_x0)],
                  "y": [queue_y0 + 0.5 * (queue_y1 - queue_y0)],
                  "mode": "markers",
                  "zorder": 2,
                  "customdata": [f"{sender}:{comm}:{item_num+1}" + "<extra></extra>"],
                  "hovertemplate":'%{customdata}',
                  "marker":
                  {
                     "size": 20,
                     "color": "rgba(0,0,0,0)"
                  },
                  "showlegend": False
               }
               queue_items.append(queue_item)
               queue_items.append(hover_info)

   def _get_graph_limits(self, node_positions, two_way_pts):

      min_x, max_x, min_y, max_y = np.Inf, -np.Inf, np.Inf, -np.Inf
      for x, y in two_way_pts:
         min_x = x if x < min_x else min_x
         max_x = x if x > max_x else max_x
         min_y = y if y < min_y else min_y
         max_y = y if y > max_y else max_y

      for _, point in node_positions.items():
         x, y = point
         min_x = x if x < min_x else min_x
         max_x = x if x > max_x else max_x
         min_y = y if y < min_y else min_y
         max_y = y if y > max_y else max_y

      return (min_x, max_x, min_y, max_y)


   def _find_normal_vectors(self, pos1, pos2, scale=1):

      diff = pos2 - pos1
      halfway = pos1 + 0.5 * diff
      dx, dy = diff[0], diff[1]
      normal1 = scale * np.array([-dy, dx]) + halfway
      normal2 = scale * np.array([dy, -dx]) + halfway

      return (normal1, normal2)

   
   def _find_points_on_curve(self, pos1, pos2, center, num_points=5):

      vector1 = pos1 - center
      vector2 = pos2 - center
      magnitude1 = np.linalg.norm(vector1)
      magnitude2 = np.linalg.norm(vector2)
      cos_theta = np.dot(vector1, vector2) / (magnitude1 * magnitude2)
      angle = np.arccos(cos_theta)
      rotation = np.sign(np.cross(vector1, vector2)).astype(int)
      increments = rotation * [angle * i / num_points for i in range(num_points)]

      points = []
      for inc in increments:
         x = np.cos(inc) * vector1[0] - np.sin(inc) * vector1[1] + center[0]
         y = np.sin(inc) * vector1[0] + np.cos(inc) * vector1[1] + center[1]
         points.append(np.array([x, y]))

      return points


   def _get_track_edges(self, track_df):

      track_edges = []
      for platform, grp in track_df.groupby(TrackDataColumns.OWNING_PLATFORM):
         recent_track_info = grp.tail(1)
         master_track_list = recent_track_info[TrackDataColumns.MASTER_TRACK_LIST].iloc[0].strip().split(" ")
         if recent_track_info[SharedColumns.EVENT_TYPE].iloc[0] == "LOCAL_TRACK_DROPPED":
            dropped_track = recent_track_info[TrackDataColumns.TRACK_ID].iloc[0]
            time_dropped = recent_track_info[SharedColumns.ISO_DATE].iloc[0]
            master_track_list.remove(dropped_track)
            cli_output.INFO(f"{self.__class__.__name__}: {dropped_track} dropped at {time_dropped}.")
         for local_track in master_track_list:
            track_grp = grp[grp[TrackDataColumns.TRACK_ID] == local_track].tail(1)
            raw_track_list = track_grp[TrackDataColumns.RAW_TRACKS].iloc[0].strip().split(" ")
            for raw_track in raw_track_list:
               contributor_name = raw_track.split(".")[0]
               if contributor_name != "no_tracks":
                  track_edges.append((contributor_name, platform))
      
      return track_edges
