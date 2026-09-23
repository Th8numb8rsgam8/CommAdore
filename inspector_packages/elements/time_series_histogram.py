from inspector_packages import *
from plotly.subplots import make_subplots
import pdb

class TimeSeriesHistogram:

   @staticmethod
   def create(frame, subplot_category, time_series_category, bin_count):

      min_time = frame["SimulationTime"].min()
      max_time = frame["SimulationTime"].max()

      num_cols = 2
      quotient, remainder = divmod(len(frame[subplot_category].unique()), num_cols)
      num_rows = quotient + remainder

      fig = make_subplots(
         rows=num_rows if num_rows >= 3 else 3,
         cols=num_cols,
         subplot_titles=frame[subplot_category].unique().astype(str),
      )

      subplot_grp = 1
      for idx, category in enumerate(frame[subplot_category].unique()):
         row, col = divmod(idx, num_cols)
         bar_data = frame[frame[subplot_category] == category]
         for _, stack_cat in enumerate(bar_data[time_series_category].unique()):
            stack = bar_data[bar_data[time_series_category] == stack_cat]
            # series = stack[bar_graph_category].value_counts()
            fig.append_trace(
               go.Histogram(
                  x=stack["SimulationTime"],
                  histfunc="count",
                  hovertemplate=f'<b>Category:</b> {stack_cat}<br>' + '<b>Count:</b> %{y}<br>' + '<b>Time:</b> %{x}' + '<extra></extra>',
                  nbinsx=bin_count,
                  xbins={
                     'start': min_time,
                     'end': max_time,
                  }
               ),
               row+1, col+1
            )
         subplot_grp += 1

      fig.update_layout(
         barmode='stack', 
         paper_bgcolor='rgba(0,0,0,0)', 
         plot_bgcolor='rgba(0,0,0,0)',
         showlegend=False)

      return fig