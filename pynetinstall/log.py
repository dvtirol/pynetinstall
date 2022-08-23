import logging


def setup_logger(name: str, level, file: str = None, format: str = "%(asctime)s - [%(levelname)s] -> %(message)s", stream: bool = False) -> None:
    logger = logging.getLogger(name)
    if file is not None:
        outp_handler = logging.FileHandler(file)
        outp_handler.setFormatter(format)
        logger.addHandler(outp_handler)
    if stream is True:
        strm_handler = logging.StreamHandler()
        strm_handler.setFormatter(format)
        logger.addHandler(strm_handler)
    logger.setLevel(level)


