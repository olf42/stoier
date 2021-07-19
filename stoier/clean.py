#!/usr/bin/env python3

import click
import logging
import yaml

from decimal import Decimal
from pathlib import Path
from stoier.log import setup_logging
from stoier.utils import get_latest_file, save_yaml

logger = logging.getLogger(__name__)


def decimal_from_postbank(value):
    return Decimal(value.replace(" \x80", "").replace(".", "").replace(",", "."))


class CleanBook():

    def __init__(self):
        self.entries = list()

    def add_entries_from_yaml(self, yaml_file, amount_col, balance_col, details_col):
        data = yaml.safe_load(yaml_file)
        for entry in data:
            entry[amount_col] = decimal_from_postbank(entry[amount_col])
            entry[balance_col] = decimal_from_postbank(entry[balance_col])
            entry[details_col] = (
                entry[details_col]
                .replace("Referenz NOTPROVIDED", "")
                .replace("Verwendungszweck", "")
            )
        self.entries.extend(data)

    def to_file(self, out_path):
        save_yaml(self.entries, out_path)


@click.command()
@click.option("-d", "--debug", is_flag=True, default=False)
@click.option("-v", "--verbose", is_flag=True, default=False)
@click.option("-b", "--amount_col", "amount_col", default="amount")
@click.option("-b", "--balance_col", "balance_col", default="balance")
@click.option("--details_col", "details_col", default="details")
@click.argument("out_dir")
@click.argument("filename")
def clean(debug, verbose, amount_col, balance_col, details_col, out_dir, filename):
    setup_logging(debug, verbose)

    c_book = CleanBook()

    filepath = get_latest_file(filename)
    logger.debug(f"Reading {filename}")
    with open(filepath) as yaml_file:
        c_book.add_entries_from_yaml(yaml_file, amount_col, balance_col, details_col)

    out_path = Path(out_dir) / "02_clean_bookings"
    if not out_path.is_dir():
        out_path.mkdir(parents=True)
    c_book.to_file(out_path)


if __name__ == "__main__":
    clean()
