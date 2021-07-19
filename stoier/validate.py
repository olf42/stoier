#!/usr/bin/env python3

import click
import logging
import yaml

from collections import defaultdict
from pathlib import Path
from stoier.log import setup_logging
from stoier.utils import get_latest_file, iterate_dated_dict, save_yaml

logger = logging.getLogger(__name__)


class ValidatedBook():

    def __init__(self):
        self.entries = defaultdict(list)

    def add_entries_from_yaml(self, yaml_file, amount_col, balance_col):
        old_balance = None
        data = yaml.load(yaml_file, Loader=yaml.Loader)
        for date_str, e, entry in iterate_dated_dict(data):
            if not old_balance:
                old_balance = entry[balance_col]
                continue
            else:
                new_balance = entry[balance_col]
                if new_balance != old_balance + entry[amount_col]:
                    logger.error(f"Balance mismatch on {date_str} in entry {entry['id']}.")
                    logger.error(f"{new_balance} != {old_balance} + {entry[amount_col]}")
                old_balance = new_balance
            out_entry = {
                "id": entry["id"],
                "vat": True,
                "vat_account": [],
                "net_accounts": [],
                "gross_accounts": []
            }
            self.entries[date_str].append(out_entry)

    def to_file(self, out_path):
        save_yaml(dict(self.entries), out_path)


@click.command()
@click.option("-d", "--debug", is_flag=True, default=False)
@click.option("-v", "--verbose", is_flag=True, default=False)
@click.option("-b", "--amount_col", "amount_col", default="amount")
@click.option("-b", "--balance_col", "balance_col", default="balance")
@click.argument("out_dir")
@click.argument("filename")
def validate(debug, verbose, amount_col, balance_col, out_dir, filename):
    setup_logging(debug, verbose)

    v_book = ValidatedBook()

    filepath = get_latest_file(filename)
    logging.debug(f"Using {filepath}")
    with open(filepath) as yaml_file:
        v_book.add_entries_from_yaml(yaml_file, amount_col, balance_col)

    out_path = Path(out_dir) / "04_valid_bookings"
    if not out_path.is_dir():
        out_path.mkdir(parents=True)
    v_book.to_file(out_path)


if __name__ == "__main__":
    validate()
