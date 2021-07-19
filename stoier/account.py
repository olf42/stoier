#!/usr/bin/env python3

import click
import logging
import yaml

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from stoier.log import setup_logging
from stoier.utils import get_latest_file, iterate_dated_dict, save_yaml

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


class AccountedBook():

    def __init__(self, vat_amount, vat_name="vat"):
        self.entries = dict()
        self.accounts = dict()
        self.vat_name = vat_name
        self.vat_amount = vat_amount

    def add_entries_from_yaml(self, data_file, assign_file):
        data = yaml.load(data_file, Loader=yaml.Loader)
        assign_data = yaml.load(assign_file, Loader=yaml.Loader)
        for date, e, entry in iterate_dated_dict(data):
            assignments = assign_data[date][e]
            types = {
                "gross": assignments["gross_accounts"],
                "net": assignments["net_accounts"]
            }
            entry["vat"] = assignments["vat"]
            for acct_type, account_list in types.items():
                for account in account_list:
                    if account not in self.accounts.keys():
                        self.accounts[account] = Account(account, acct_type)
                    self.accounts[account].add_booking(entry)

            # Handle VAT
            if self.vat_name not in self.accounts.keys():
                self.accounts[self.vat_name] = Account(self.vat_name, "vat")
            self.accounts[self.vat_name].add_booking(entry)

        self.entries.update(data)

    def to_files(self, out_path, now):
        for name, account in self.accounts.items():
            save_yaml(account.bookings, out_path, prefix=f"{name}_", date=now)


@click.command()
@click.option("-d", "--debug", is_flag=True, default=False)
@click.option("-v", "--verbose", is_flag=True, default=False)
@click.option("--amount_col", "amount_col", default="amount")
@click.option("--vat_col", "vat_col", default="vat")
@click.option("--vat", "vat_amount", default=19)
@click.argument("out_dir")
@click.argument("data_filename")
@click.argument("assign_filename")
def account(
    debug,
    verbose,
    vat_amount,
    amount_col,
    vat_col,
    out_dir,
    data_filename,
    assign_filename
):
    setup_logging(debug, verbose)

    a_book = AccountedBook(vat_amount)

    filepath = get_latest_file(data_filename)

    assign_filepath = get_latest_file(assign_filename)
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
    a_book.to_files(out_path, now)


if __name__ == "__main__":
    account()
