import time
from functools import wraps

TIMER_ENABLED = False

def timer(func):
    """Measure and print the execution time of a function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if TIMER_ENABLED:
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time
            print(f"Function {func.__name__!r} took {elapsed_time:.4f} seconds")
            return result
        else:
            return func(*args, **kwargs)
    return wrapper