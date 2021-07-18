#!/usr/bin/env python3

import click
import logging
import yaml

from collections import defaultdict
from pathlib import Path
from stoier.log import setup_logging
from stoier.utils import get_date, save_yaml

logger = logging.getLogger(__name__)


class UniqueBook():

    def __init__(self):
        self.entries = defaultdict(list)
        self.known_hashes = set()

    def add_entries_from_yaml(self, yaml_file, start, end, datecol, date_format):
        data = yaml.safe_load(yaml_file)
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

            # Order by date
            entries_list = self.entries[entry_date.strftime("%Y-%m-%d")]
            entry["id"] = len(entries_list)
            entries_list.append(entry)

    def to_file(self, out_path):
        save_yaml(dict(self.entries), out_path)


@click.command()
@click.option("-d", "--debug", is_flag=True, default=False)
@click.option("-v", "--verbose", is_flag=True, default=False)
@click.option("-f", "--format", "date_format", default="%d.%m.%Y")
@click.option("-s", "--start", "start_str", default=None)
@click.option("--datecol", "datecol", default=None)
@click.option("-e", "--end", "end_str", default=None)
@click.argument("out_dir")
@click.argument("filenames", nargs=-1)
def deduplicate(
        debug, verbose, out_dir, start_str, end_str, date_format, filenames, datecol
):
    setup_logging(debug, verbose)
    start = get_date(start_str, date_format)
    end = get_date(end_str, date_format)

    u_book = UniqueBook()
    for filename in filenames:
        logging.debug(filename)
        with open(filename) as yaml_file:
            u_book.add_entries_from_yaml(yaml_file, start, end, datecol, date_format)

    out_path = Path(out_dir) / "02_unique_bookings"
    if not out_path.is_dir():
        out_path.mkdir(parents=True)
    u_book.to_file(out_path)


if __name__ == "__main__":
    deduplicate()
