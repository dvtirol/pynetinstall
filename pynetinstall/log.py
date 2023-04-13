import logging


class Logger:
    """
    Logger object manages logging for the different Levels

    Attributes
    ----------

    quiet : bool
        When set to True no logs will be (default: False)
    debug_logger : logging.Logger
        Logs Records with the Debug Level (10)
    info_logger : logging.Logger
        Logs Records with the Info Level (20)
    error_logger : logging.Logger
        Logs Records with the Error Level (40)

    Methods
    -------

    debug(message, force=False) -> None
        Log a message to the `debug_logger`

    info(message, force=False) -> None
        Log a message to the `info_logger`

    error(message, force=False) -> None
        Log a message to the `error_logger` 

    set_level(level) -> None
        Update the Level of each logger
    """
    quiet: bool = False

    def __init__(self, level: int = logging.INFO) -> None:
        """
        Initialize a new Logger object

        Argument
        --------
        level : int
            What level should be logged from the Logger (default: logging.INFO)
        """
        self.debug_logger: logging.Logger = logging.getLogger("pynet-deb")
        self.info_logger: logging.Logger = logging.getLogger("pynet-inf")
        self.error_logger: logging.Logger = logging.getLogger("pynet-err")
        
        self.set_level(level)

    def debug(self, message: str, force: bool = False) -> None:
        """
        Log Records to the `debug_logger`

        Arguments
        ---------

        message : str
            The message to log
        force : bool
            If the message should be logged even if the `quiet` Attribute is set to True (default: False)
        """
        if not self.quiet or force:
            self.debug_logger.debug(message)

    def info(self, message: str, force: bool = False) -> None:
        """
        Log Records to the `info_logger`

        Arguments
        ---------

        message : str
            The message to log
        force : bool
            If the message should be logged even if the `quiet` Attribute is set to True (default: False)
        """
        if not self.quiet or force:
            self.info_logger.info(message)

    def error(self, message: str, force: bool = False) -> None:
        """
        Log Records to the `error_logger`

        Arguments
        ---------

        message : str
            The message to log
        force : bool
            If the message should be logged even if the `quiet` Attribute is set to True (default: False)
        """
        if not self.quiet or force:
            self.error_logger.error(message)

    def set_level(self, level: int) -> None:
        """
        Update the Level of each logger

        Argument
        --------

        level : int
            The level to update the Loggers to 
        """
        self.debug_logger.setLevel(level)
        self.error_logger.setLevel(level)
        self.info_logger.setLevel(level)
