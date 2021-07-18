#!/usr/bin/env python3

import click
import csv
import logging

from pathlib import Path
from stoier.log import setup_logging
from stoier.utils import save_yaml

logger = logging.getLogger(__name__)


class Book:

    def __init__(self, entries=None):
        self.entries = []
        if entries:
            self.add_entries(entries)

    def add_entry(self, entry):
        self.entries.append(entry)

    def add_entries_from_csv(self, csv_file, skip=0, trigger=None, header=True):
        reader = csv.reader(csv_file, delimiter=";")
        logger.debug(f"Using trigger: {trigger}")
        n_entries = 0
        for r, row in enumerate(reader):
            if trigger:
                if not row:
                    continue
                logger.debug(f"{r}: {row}")
                if row[trigger[0]] == trigger[1] and row:
                    skip = r + trigger[2]
                    logger.debug(
                        f"Skipped {r} rows until trigger found. Starting in {trigger[2]} rows."
                    )
                    trigger = None
                else:
                    continue
            if r < skip:
                continue
            if r == skip:
                if not header:
                    header = row
                    logger.debug(f"Found header: {header}")
                    continue
                else:
                    logger.debug(f"Using custom header: {header}")
            n_entries += 1
            self.add_entry(dict(zip(header, row)))
        logger.info(f"{n_entries} entries (total: {len(self.entries)}) added from csv file.")

    def to_file(self, out_path):
        save_yaml(self.entries, out_path)


def get_trigger(trigger_str):
    """
    Parse trigger string COL_ID_TO_CHECK:STRING_TO_FIND:[SKIP_N_ROWS_AFTER_FIND]
    """
    if not trigger_str:
        return None

    trigger = trigger_str.split(":")
    if len(trigger) < 2 or len(trigger) > 3:
        raise ValueError(f"{trigger_str} must contain 2<=n<=3 elements.")
    trigger[0] = int(trigger[0])
    if len(trigger) == 2:
        trigger[2] = 0
    else:
        trigger[2] = int(trigger[2])
    logger.debug(f"Trigger: {trigger}")
    return trigger


def get_header(header_str):
    if not header_str:
        return None
    return header_str.split(":")


@click.command()
@click.option("-s", "--skip", default=0)
@click.option("-h", "--header", "header_str", default=None)
@click.option("-t", "--trigger", "trigger_str", default=None)
@click.option("-e", "--encoding", default="iso-8859-1")
@click.option("-d", "--debug", is_flag=True, default=False)
@click.option("-v", "--verbose", is_flag=True, default=False)
@click.argument("out_dir")
@click.argument("csv_filenames", nargs=-1)
def csv_to_yml(
        debug, verbose, header_str, trigger_str, skip, encoding, out_dir, csv_filenames
):
    setup_logging(debug, verbose)

    trigger = get_trigger(trigger_str)
    header = get_header(header_str)
    book = Book()

    for csv_filename in csv_filenames:
        logging.debug(csv_filename)
        with open(csv_filename, encoding=encoding) as csv_file:
            book.add_entries_from_csv(csv_file, skip, trigger, header)

    out_path = Path(out_dir) / "01_bookings"
    if not out_path.is_dir():
        out_path.mkdir(parents=True)
    book.to_file(out_path)


if __name__ == "__main__":
    csv_to_yml()
