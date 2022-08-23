import logging


class Logger:
    debug_logger: logging.Logger
    error_logger: logging.Logger
    info_logger: logging.Logger

    def __init__(self) -> None:
        self.debug_logger = logging.getLogger("pynet-deb")
        self.error_logger = logging.getLogger("pynet-err")
        self.info_logger = logging.getLogger("pynet-inf",)


    def info(self, message: str) -> None:
        self.info_logger.info(message)

    def error(self, message: str) -> None:
        self.error_logger.error(message)
    
    def debug(self, message: str) -> None:
        self.debug_logger.debug(message)
