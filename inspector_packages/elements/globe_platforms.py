import pandas as pd
from datetime import datetime, timezone
from utils import cli_output


class GlobePlatforms:

   def __init__(self, df):

      self._df = df

   def get_platform_states(self, time_val):

      time_diff = self._df["Timestamp"] - time_val
      time_states = time_diff <= 0
      prev = time_states[time_states == True].index
      next = time_states[time_states == False].index

      if not prev.empty and not next.empty:
         prev_idx = time_diff[time_diff == time_diff[prev].max()].index
         next_idx = time_diff[time_diff == time_diff[next].min()].index
         prev_df = self._df.iloc[prev_idx].reset_index(drop=True)
         next_df = self._df.iloc[next_idx].reset_index(drop=True)
         interpolated_df = self._interpolate_platform_states(prev_df, next_df, time_val)
         return interpolated_df

      elif prev.empty and not next.empty:
         next_idx = time_diff[time_diff == time_diff[next].min()].index
         next_df = self._df.iloc[next_idx]
         return next_df

      elif not prev.empty and next.empty:
         prev_idx = time_diff[time_diff == time_diff[prev].max()].index
         prev_df = self._df.iloc[prev_idx]
         return prev_df

      else:
         cli_output.WARNING(f"No platform state was returned for {time_val}.")
         return None


   def _interpolate_platform_states(self, prev_df, next_df, time_val):

      if prev_df.shape[0] != next_df.shape[0]:
         s1 = prev_df["Platform_Name"]
         s2 = next_df["Platform_Name"]
         prev_not_next = s1[~s1.isin(s2)]
         next_not_prev = s2[~s2.isin(s1)]

         prev_iso = prev_df["ISODate"].unique()[0]
         next_iso = next_df["ISODate"].unique()[0]
         if not prev_not_next.empty:
            platforms = " ".join(prev_not_next.to_list())
            cli_output.WARNING(f"Platforms removed between {prev_iso} and {next_iso}: {platforms}")
            prev_df = prev_df[~prev_df["Platform_Name"].isin(prev_not_next)].reset_index(drop=True)

         if not next_not_prev.empty:
            platforms = " ".join(next_not_prev.to_list())
            cli_output.WARNING(f"Platforms added between {prev_iso} and {next_iso}: {platforms}")
            next_df = next_df[~next_df["Platform_Name"].isin(next_not_prev)].reset_index(drop=True)

      interpolated_df = prev_df
      prev_time = prev_df["Timestamp"].unique()[0]
      next_time = next_df["Timestamp"].unique()[0]
      delta = (time_val - prev_time) / (next_time - prev_time)
      prev_pos = prev_df[["Location_X", "Location_Y", "Location_Z"]]
      next_pos = next_df[["Location_X", "Location_Y", "Location_Z"]]
      current_pos = prev_pos + delta * (next_pos - prev_pos)
      current_time = prev_time + delta * (next_time - prev_time)
      current_iso = datetime.fromtimestamp(current_time, tz=timezone.utc).isoformat()

      interpolated_df["Timestamp"] = current_time
      interpolated_df["ISODate"] = current_iso
      interpolated_df[["Location_X", "Location_Y", "Location_Z"]] = current_pos

      return interpolated_df