#!/usr/bin/env python3

import click
import csv
import logging
import yaml

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from stoier.log import setup_logging
from stoier.utils import (
    get_latest_file,
    iterate_dated_dict,
    save_yaml,
    NotADateError,
    NotADirError
)

logger = logging.getLogger(__name__)

ROUND = 3


class Account():

    types = ("net", "gross", "vat")

    def __init__(self, name, acct_type, amount_col="amount", vat_col="vat", vat_amount=19):
        self.acct_type = acct_type
        self.amount_col = amount_col
        self.bookings = list()
        self.name = name
        self.vat_col = vat_col
        self.vat_amount = vat_amount

    def sum(self):
        acct_amount_col = f"{self.acct_type}_amount"
        return sum([b[acct_amount_col] for b in self.bookings])

    def add_booking(self, booking):
        b = booking.copy()
        logger.debug(b)
        if self.acct_type == "net":
            vat = b[self.vat_col]
            if vat is True:
                b["net_amount"] = round(
                    b[self.amount_col] * (Decimal(100) / (100 + self.vat_amount)), ROUND
                )
            elif isinstance(vat, Decimal):
                b["net_amount"] = round(b[self.amount_col] - vat, ROUND)
            elif isinstance(vat, int):
                b["net_amount"] = round(b[self.amount_col] * (Decimal(100) / (100 + vat)), ROUND)
        elif self.acct_type == "vat":
            vat = b[self.vat_col]
            if vat is True:
                b["vat_amount"] = round(
                    b[self.amount_col] * (Decimal(self.vat_amount) / (100 + self.vat_amount)),
                    ROUND
                )
            elif isinstance(vat, Decimal):
                b["vat_amount"] = round(vat, ROUND)
            elif isinstance(vat, int):
                b["vat_amount"] = round(
                    b[self.amount_col] * (Decimal(vat) / (100 + vat)), ROUND
                )
        else:
            b["gross_amount"] = b[self.amount_col]
        self.bookings.append(b)
        return b

    def serialize(self):
        return {
            "name": self.name,
            "type": self.acct_type,
            "bookings": self.bookings
        }


class AccountedBook():

    default_header = ['date_1', 'sender', 'receiver', 'type', 'details', 'amount', 'balance']

    def __init__(self, vat_amount, vat_name="vat", header=None):
        self.entries = dict()
        self.accounts = dict()
        self.vat_name = vat_name
        self.vat_amount = vat_amount
        self.spreadsheet = list()
        if header is None:
            self.header = self.default_header.copy()
        else:
            self.header = header

    def all_accounts(self, assign_data):
        accounts = set()
        vat_percentages = set()
        for date, e, entry in iterate_dated_dict(assign_data):
            for acct_type in ("gross_accounts", "net_accounts"):
                for acct in entry[acct_type]:
                    accounts.add(acct)
                    vat_percentages.add(entry["vat"])
                    yield (acct, acct_type.split("_")[0])
        # Return a VAT account name for each VAT percentage encountered and one for unknown
        # percentages
        for vat_percentage in vat_percentages:
            yield (f"{self.vat_name}_{vat_percentage}", "vat")
        yield (self.vat_name, "vat")

    def add_entries_from_yaml(self, data_file, assign_file):
        data = yaml.load(data_file, Loader=yaml.Loader)
        assign_data = yaml.load(assign_file, Loader=yaml.Loader)
        self.accounts = {
            acct: Account(acct, acct_type) for acct, acct_type in self.all_accounts(assign_data)
        }
        for date, e, entry in iterate_dated_dict(data):
            logging.debug(entry)
            # row for csv export
            row = {h: entry[h] for h in self.header}
            row.update(
                dict.fromkeys(
                    list(self.accounts.keys()), None
                )
            )

            assignments = assign_data[date][e]
            types = {
                "gross": assignments["gross_accounts"],
                "net": assignments["net_accounts"]
            }
            entry["vat"] = assignments["vat"]
            for acct_type, account_list in types.items():
                for account in account_list:
                    booked_entry = self.accounts[account].add_booking(entry)
                    row[account] = booked_entry[f"{acct_type}_amount"]

            # Handle VAT
            vat = entry["vat"]
            if isinstance(vat, int):
                booked_entry = self.accounts[f"{self.vat_name}_{str(vat)}"].add_booking(entry)
                row[f"{self.vat_name}_{str(vat)}"] = booked_entry["vat_amount"]
            else:
                booked_entry = self.accounts[self.vat_name].add_booking(entry)
                row[self.vat_name] = booked_entry["vat_amount"]

            self.spreadsheet.append(row)
        self.entries.update(data)

    def to_files(self, out_path, now, no_gross_csv):
        for name, account in self.accounts.items():
            save_yaml(account.serialize(), out_path, prefix=f"{name}_", date=now)

        if no_gross_csv:
            csv_accounts = []
            for acct_name, acct in self.accounts.items():
                if acct.acct_type != "gross":
                    csv_accounts.append(acct_name)
        else:
            csv_accounts = list(self.accounts.keys())
        csv_path = out_path / f"{now.isoformat()}.csv"
        with open(csv_path, "w") as csv_file:
            fieldnames = self.header + csv_accounts
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(self.spreadsheet)
        logger.info(f"Written {len(self.spreadsheet)} lines to {csv_path}")


@click.command()
@click.option("-d", "--debug", is_flag=True, default=False)
@click.option("-v", "--verbose", is_flag=True, default=False)
@click.option("--amount_col", "amount_col", default="amount")
@click.option("--vat_col", "vat_col", default="vat")
@click.option("--vat", "vat_amount", default=19)
@click.option("-h", "--header", "header_str", default=None)
@click.option(
    "--no-gross-csv", help="Exclude gross accounts from csv export", is_flag=True, default=False
)
@click.argument("out_dir")
@click.argument("data_filename")
@click.argument("assign_filename")
def account(
    debug,
    verbose,
    vat_amount,
    amount_col,
    vat_col,
    header_str,
    no_gross_csv,
    out_dir,
    data_filename,
    assign_filename
):
    setup_logging(debug, verbose)

    if header_str:
        header = header_str.split(":")
    else:
        header = None
    a_book = AccountedBook(vat_amount, header=header)

    try:
        filepath = get_latest_file(data_filename)
        assign_filepath = get_latest_file(assign_filename)
    except (NotADateError, NotADirError) as e:
        logger.error(e)
        exit(1)

    logger.debug(f"Using {filepath} as datafile.")
    logger.debug(f"Using {assign_filepath} as assign file.")
    with (
        open(filepath) as data_file,
        open(assign_filepath) as assign_file
    ):
        a_book.add_entries_from_yaml(data_file, assign_file)

    now = datetime.now()
    out_path = Path(out_dir) / "05_accounts" / now.isoformat()
    if not out_path.is_dir():
        out_path.mkdir(parents=True)
    a_book.to_files(out_path, now, no_gross_csv)


if __name__ == "__main__":
    account()
