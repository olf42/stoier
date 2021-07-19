#!/usr/bin/env python3

import logging

LOG_FORMAT = {
    logging.WARNING: "%(message)s",
    logging.INFO: "%(message)s",
    logging.DEBUG: "%(levelname)s: %(message)s"
}

logger = logging.getLogger(__name__)


def setup_logging(debug, verbose):
    level = get_loglevel(debug, verbose)
    logging.basicConfig(level=level, format=LOG_FORMAT[level])


def get_loglevel(debug, verbose):
    if debug:
        return logging.DEBUG
    elif verbose:
        return logging.INFO
    else:
        return logging.WARNING
