#!/usr/bin/env python3

import click
import logging
import yaml

from datetime import datetime
from pprint import pprint
from stoier.log import setup_logging
from stoier.utils import get_latest_file, iterate_dated_dict

logger = logging.getLogger(__name__)


@click.command()
@click.option("-f", "--format", "date_format", default="%d.%m.%Y")
@click.option("-s", "--start", "start_str", default=None)
@click.option("-e", "--end", "end_str", default=None)
@click.option("-d", "--debug", is_flag=True, default=False)
@click.option("-v", "--verbose", is_flag=True, default=False)
@click.argument("filename")
def iterate(debug, verbose, date_format, start_str, end_str, filename):
    setup_logging(debug, verbose)

    filepath = get_latest_file(filename)
    logging.debug(f"Using {filepath}")

    with open(filepath) as yaml_file:
        data = yaml.load(yaml_file, Loader=yaml.Loader)
    for date_str, e, entry in iterate_dated_dict(
        data, start=datetime.strptime(start_str, date_format)
    ):
        pprint(entry)
        input()


if __name__ == "__main__":
    iterate()
