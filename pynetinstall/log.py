import logging


class Logger:
    debug_logger: logging.Logger
    error_logger: logging.Logger
    info_logger: logging.Logger

    quiet: bool = False

    def __init__(self, level: int = logging.INFO) -> None:
        self.debug_logger = logging.getLogger("pynet-deb")
        self.error_logger = logging.getLogger("pynet-err")
        self.info_logger = logging.getLogger("pynet-inf")
        self.set_level(level)


    def info(self, message: str) -> None:
        if not self.quiet:
            self.info_logger.info(message)

    def error(self, message: str) -> None:
        if not self.quiet:
            self.error_logger.error(message)
    
    def debug(self, message: str) -> None:
        if not self.quiet:
            self.debug_logger.debug(message)

    def set_level(self, level: int) -> None:
        self.debug_logger.setLevel(level)
        self.error_logger.setLevel(level)
        self.info_logger.setLevel(level)
