import pandas as pd
from utils import cli_output
from ..mission_execution import *


class GlobePlatforms:

   def __init__(self, db):

      self._db = db 
      self._cursor = self._db.cursor()

   def get_platform_states(self, time_val):

      prev_time = self._cursor.execute(f'''
         SELECT {SharedColumns.SIMULATION_TIME}
         FROM {PLATFORM_DATA_TABLE}
         WHERE {SharedColumns.SIMULATION_TIME} <= {time_val}
         ORDER BY {SharedColumns.SIMULATION_TIME} DESC LIMIT 1
         ''').fetchone()

      next_time = self._cursor.execute(f'''
         SELECT {SharedColumns.SIMULATION_TIME}
         FROM {PLATFORM_DATA_TABLE}
         WHERE {SharedColumns.SIMULATION_TIME} > {time_val}
         ORDER BY {SharedColumns.SIMULATION_TIME} ASC LIMIT 1
         ''').fetchone()

      if prev_time is not None and next_time is not None:
         prev_df = self._retrieve_data(prev_time[0])
         next_df = self._retrieve_data(next_time[0])
         interpolated_df = self._interpolate_platform_states(prev_df, next_df, time_val)
         return interpolated_df

      elif prev_time is None and next_time is not None:
         return self._retrieve_data(next_time[0])

      elif prev_time is not None and next_time is None:
         return self._retrieve_data(prev_time[0])

      else:
         cli_output.WARNING(f"{self.__class__.__name__}: No platform state was returned for {time_val}.")
         return None

   def _retrieve_data(self, time_val):
      df = pd.read_sql_query(
         sql=f'''
         SELECT * FROM {PLATFORM_DATA_TABLE}
         WHERE {SharedColumns.SIMULATION_TIME} = {time_val}
         ''', 
         con=self._db, 
         index_col=PlatformDataColumns.PLATFORM_NAME)\
         .astype(PANDAS_PLATFORM_DATA_TYPES)
      return df

   def _interpolate_platform_states(self, prev_df, next_df, time_val):

      if prev_df.shape[0] != next_df.shape[0]:
         prev_not_next = prev_df.index.difference(next_df.index)
         next_not_prev = next_df.index.difference(prev_df.index)

         prev_iso = prev_df[SharedColumns.ISO_DATE].unique()[0]
         next_iso = next_df[SharedColumns.ISO_DATE].unique()[0]
         if not prev_not_next.empty:
            platforms = " ".join(prev_not_next.to_list())
            cli_output.WARNING(f"{self.__class__.__name__}: Platforms removed between {prev_iso} and {next_iso}: {platforms}")
            prev_df = prev_df[~prev_df.index.isin(prev_not_next)]

         if not next_not_prev.empty:
            platforms = " ".join(next_not_prev.to_list())
            cli_output.WARNING(f"{self.__class__.__name__}: Platforms added between {prev_iso} and {next_iso}: {platforms}")
            next_df = next_df[~next_df.index.isin(next_not_prev)]

      interpolated_df = prev_df
      prev_time = prev_df[SharedColumns.SIMULATION_TIME].unique()[0]
      next_time = next_df[SharedColumns.SIMULATION_TIME].unique()[0]
      delta = (time_val - prev_time) / (next_time - prev_time)
      prev_pos = prev_df[[PlatformDataColumns.LOCATION_X, PlatformDataColumns.LOCATION_Y, PlatformDataColumns.LOCATION_Z]]
      next_pos = next_df[[PlatformDataColumns.LOCATION_X, PlatformDataColumns.LOCATION_Y, PlatformDataColumns.LOCATION_Z]]
      current_pos = prev_pos + delta * (next_pos - prev_pos)
      current_time = prev_time + delta * (next_time - prev_time)

      interpolated_df.loc[:, SharedColumns.SIMULATION_TIME] = current_time
      interpolated_df.loc[:, [PlatformDataColumns.LOCATION_X, PlatformDataColumns.LOCATION_Y, PlatformDataColumns.LOCATION_Z]] = current_pos

      return interpolated_df