#!/usr/bin/env python3

import click
import logging
import yaml

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from stoier.log import setup_logging
from stoier.utils import get_date, get_latest_file, save_yaml

logger = logging.getLogger(__name__)


class UniqueBook():

    def __init__(self):
        self.entries = defaultdict(list)
        self.known_hashes = set()
        self.accounts = set()

    def add_entries_from_yaml(self, yaml_file, start, end, datecol, date_format):
        data = yaml.load(yaml_file, Loader=yaml.Loader)
        for entry in data:

            # Hashing and Deduplication
            entry_hash = hash(frozenset(entry.items()))
            if entry_hash in self.known_hashes:
                continue
            else:
                self.known_hashes.add(entry_hash)

            entry_date = get_date(entry[datecol], date_format)

            # Date Filtering
            if start and entry_date < start:
                continue
            if end and entry_date > end:
                continue

            self.accounts.add(entry["sender"])

            # Order by date
            entries_list = self.entries[entry_date.strftime("%Y-%m-%d")]
            entry["id"] = len(entries_list)
            entries_list.append(entry)

    def to_file(self, out_path, date=None):
        save_yaml(dict(self.entries), out_path, date=date)

    def save_accounts(self, out_path, date=None):
        save_yaml(dict.fromkeys(self.accounts), out_path, prefix="accounts_", date=date)


@click.command()
@click.option("-d", "--debug", is_flag=True, default=False)
@click.option("-v", "--verbose", is_flag=True, default=False)
@click.option("-f", "--format", "date_format", default="%d.%m.%Y")
@click.option("-s", "--start", "start_str", default=None)
@click.option("--date_col", "date_col", default="date_1")
@click.option("-e", "--end", "end_str", default=None)
@click.option("-a", "--with-account-mapping", "with_account_mapping", is_flag=True, default=True)
@click.argument("out_dir")
@click.argument("filename")
def deduplicate(
    debug,
    verbose,
    out_dir,
    start_str,
    end_str,
    date_format,
    filename,
    date_col,
    with_account_mapping
):
    setup_logging(debug, verbose)
    start = get_date(start_str, date_format)
    end = get_date(end_str, date_format)

    u_book = UniqueBook()
    filepath = get_latest_file(filename)
    logger.debug(f"Reading {filepath}")
    with open(filepath) as yaml_file:
        u_book.add_entries_from_yaml(yaml_file, start, end, date_col, date_format)

    out_path = Path(out_dir) / "03_unique_bookings"
    if not out_path.is_dir():
        out_path.mkdir(parents=True)

    now = datetime.now()
    u_book.to_file(out_path, date=now)
    if with_account_mapping:
        u_book.save_accounts(out_path, date=now)


if __name__ == "__main__":
    deduplicate()
