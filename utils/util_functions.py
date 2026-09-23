import time
import ctypes
from ctypes import wintypes
from functools import wraps
from .cli_args import cli_output

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
            cli_output.OK(f"Function {func.__name__!r} took {elapsed_time:.4f} seconds")
            return result
        else:
            return func(*args, **kwargs)
    return wrapper

class WindowsFileAPI:

    GENERIC_READ = 0x80000000
    GENERIC_WRITE = 0x40000000
    FILE_SHARE_NONE = 0x00000000 # Do not share read/write/delete
    OPEN_EXISTING = 3
    FILE_ATTRIBUTE_NORMAL = 0x80

    @staticmethod
    def check_permission(file_path):

        # Load kernel32
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

        # Setup CreateFileW
        CreateFileW = kernel32.CreateFileW
        CreateFileW.argtypes = [
            wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
            ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p
        ]
        CreateFileW.restype = wintypes.HANDLE

        # Attempt to open file without sharing permissions
        handle = CreateFileW(
            file_path,
            WindowsFileAPI.GENERIC_READ | WindowsFileAPI.GENERIC_WRITE,
            WindowsFileAPI.FILE_SHARE_NONE,  # <--- Crucial part
            None,
            WindowsFileAPI.OPEN_EXISTING,
            WindowsFileAPI.FILE_ATTRIBUTE_NORMAL,
            None
        )

        handle = ctypes.c_int32(handle).value
        if handle == -1: # INVALID_HANDLE_VALUE
            error = ctypes.get_last_error()
            if error == 32: # ERROR_SHARING_VIOLATION
                raise PermissionError(f"Mission holds lock: {file_path}")
            raise OSError(f"Failed to open file {file_path}, error code: {error}")
        
        kernel32.CloseHandle(handle)