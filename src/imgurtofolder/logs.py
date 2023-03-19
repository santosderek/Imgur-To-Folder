import logging

"""
Level | Numeric value

CRITICAL 50
ERROR 40
WARNING 30
INFO 20
DEBUG 10
NOTSET 0
"""
class Log:
    def __init__(self, name, level=logging.INFO):
        self._log = logging.getLogger(name)

        # Log itself should always be DEBUG while handlers should be whatever.
        # This will allow all logs to be passed,
        # but handlers "handle" what's shown.
        self._log.setLevel(logging.DEBUG)

        # Each logger will have the same format
        format_log = '[%(name)s](%(levelname)s) %(asctime)s: %(message)s'
        format_date = '%I:%M:%S %p'
        self._formatter = logging.Formatter(format_log, datefmt=format_date)

        # Handler for screen output
        self._stream_handler = logging.StreamHandler()
        self._stream_handler.setLevel(level)
        self._stream_handler.setFormatter(self._formatter)
        self._log.addHandler(self._stream_handler)

    def set_level(self, level):
        self._log.setLevel(level)
        self._stream_handler.setLevel(level)

    def set_debug(self):
        self.set_level(10)

    def set_info(self):
        self.set_level(20)

    def set_warning(self):
        self.set_level(30)

    def set_error(self):
        self.set_level(40)

    def set_critical(self):
        self.set_level(50)

    def critical(self, message, **kwargs):
        self._log.critical(message, **kwargs)

    def error(self, message, **kwargs):
        self._log.error(message, **kwargs)

    def warning(self, message, **kwargs):
        self._log.warning(message, **kwargs)

    def info(self, message, **kwargs):
        self._log.info(message, **kwargs)

    def exception(self, message):
        self._log.exception(message)

    def debug(self, message, **kwargs):
        self._log.debug(message, **kwargs)
