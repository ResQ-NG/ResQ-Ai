class Status:
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


import sys

class Logger:

    def __init__(self, mode):
      self.mode = mode
      self.colors = {
          Status.SUCCESS: "\033[92m",  # Green
          Status.ERROR: "\033[91m",    # Red
          Status.WARNING: "\033[93m",  # Yellow
          Status.INFO: "\033[94m",     # Blue
          Status.DEBUG: "\033[95m",    # Magenta
          "RESET": "\033[0m"           # Reset color
      }

    def log(self, message: str, status):
      if self.mode == "DEBUG":
         color = self.colors.get(status, "")
         reset = self.colors["RESET"]
         print(f"{color}{message}{reset}")



#Todo: use env later for this--
main_logger = Logger("DEBUG")
