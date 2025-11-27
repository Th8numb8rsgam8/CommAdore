import sys
import warnings
import numpy as np
from utils import cli_output

class GlobeMethods:

   EQUATOR_RADIUS = 6.378 * 10**6
   POLAR_RADIUS = 6.357 * 10**6

   ARROWS_SCALING = [
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

   @staticmethod
   def get_curve_points_on_sphere(point1, point2, num_points=50):
      """
      Calculates points along the great-circle curve between two points on a sphere.

      Args:
          point1: Tuple (x, y, z) coordinates of the first point.
          point2: Tuple (x, y, z) coordinates of the second point.
          num_points: Number of points to generate along the curve.

      Returns:
          A list of tuples, where each tuple is (x, y, z) coordinates of a point on the curve.
      """

      # Calculate the angle between the two points
      vector_dot = np.dot(point1, point2)
      vector_magnitudes_mult = np.linalg.norm(point1) * np.linalg.norm(point2)
      angle = np.arccos(vector_dot / vector_magnitudes_mult)

      # Generate points along the great-circle curve
      x, y, z = [], [], []
      for i in range(num_points+1):
          t = i / num_points
          new_angle = angle * t
          sin_angle = np.sin(new_angle)
          sin_remaining_angle = np.sin(angle - new_angle)
          
          new_point = (sin_remaining_angle * point1 + sin_angle * point2) / np.sin(angle)
          x.append(new_point[0])
          y.append(new_point[1])
          z.append(new_point[2])

      return x, y, z


   @staticmethod
   def get_points_on_line_segment(point1, point2, num_points=50):

      x, y, z = [], [], []
      for i in range(num_points+1):
         t = i / num_points
         new_point = (1 - t) * point1 + t * point2
         x.append(new_point[0])
         y.append(new_point[1])
         z.append(new_point[2])

      return x, y, z


   @staticmethod
   def los_hits_horizon(sender_location, receiver_location):

      diff = receiver_location - sender_location
      t = -(sender_location * diff).sum() / (diff ** 2).sum()

      if 0 < t < 1:
         closest_point = sender_location + t * diff
         return np.linalg.norm(closest_point) <= GlobeMethods.EQUATOR_RADIUS
      else:
         return False
   
   @staticmethod
   def create_transmission_line(
      sender_location, receiver_location, 
      sender_name, receiver_name,
      platform_range):

      line_data = {}

      interval = None
      scaling = None
      for rng_step in GlobeMethods.ARROWS_SCALING:
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
            cli_output.WARNING(f"NO transmission line from {sender_name} to {receiver_name}.")
            line_data.update({
               "x": [sender_location[0], receiver_location[0]],
               "y": [sender_location[1], receiver_location[1]],
               "z": [sender_location[2], receiver_location[2]],
            })
            return line_data

      return line_data