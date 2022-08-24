import logging


class Logger:
    debug_logger: logging.Logger
    error_logger: logging.Logger
    info_logger: logging.Logger
    step_logger: logging.Logger

    quiet: bool = False

    def __init__(self, level: int = logging.INFO) -> None:
        self.debug_logger = logging.getLogger("pynet-deb")
        self.error_logger = logging.getLogger("pynet-err")
        self.info_logger = logging.getLogger("pynet-inf")
        self.step_logger = logging.getLogger("pynet-stp")
        self.set_level(level)


    def info(self, message: str, force: bool = False) -> None:
        if not self.quiet or force:
            self.info_logger.info(message)

    def error(self, message: str, force: bool = False) -> None:
        if not self.quiet or force:
            self.error_logger.error(message)
    
    def debug(self, message: str, force: bool = False) -> None:
        if not self.quiet or force:
            self.debug_logger.debug(message)

    def step(self, message: str, force: bool = False) -> None:
        if not self.quiet or force:
            self.step_logger.log(15, message)

    def set_level(self, level: int) -> None:
        self.debug_logger.setLevel(level)
        self.error_logger.setLevel(level)
        self.info_logger.setLevel(level)
        self.step_logger.setLevel(level)
