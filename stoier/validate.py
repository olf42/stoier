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

    def __init__(self, accounts):
        self.entries = defaultdict(list)
        self.accounts = accounts

    def add_entries_from_yaml(
            self, data_file, amount_col, balance_col, sender_col, net_account_name
    ):
        old_balance = None
        data = yaml.load(data_file, Loader=yaml.Loader)
        for date_str, e, entry in iterate_dated_dict(data):
            if self.accounts:
                gross_account = self.accounts.get(entry[sender_col], None)
            gross_accounts = [gross_account] if gross_account else []
            net_accounts = [net_account_name] if gross_account else []
            out_entry = {
                "id": entry["id"],
                "vat": True,
                "net_accounts": net_accounts,
                "gross_accounts": gross_accounts
            }
            self.entries[date_str].append(out_entry)

            if not old_balance:
                old_balance = entry[balance_col]
                continue
            else:
                new_balance = entry[balance_col]
                if new_balance != old_balance + entry[amount_col]:
                    logger.error(f"Balance mismatch on {date_str} in entry {entry['id']}.")
                    logger.error(f"{new_balance} != {old_balance} + {entry[amount_col]}")
                old_balance = new_balance

    def to_file(self, out_path):
        save_yaml(dict(self.entries), out_path)


@click.command()
@click.option("-d", "--debug", is_flag=True, default=False)
@click.option("-v", "--verbose", is_flag=True, default=False)
@click.option("-a", "--amount_col", "amount_col", default="amount")
@click.option("-b", "--balance_col", "balance_col", default="balance")
@click.option("-s", "--sender_col", "sender_col", default="sender")
@click.option("-n", "--net_account_name", "net_account_name", default="earnings")
@click.option("--accounts", "acct_filename", default=None)
@click.argument("out_dir")
@click.argument("filename")
def validate(
    debug,
    verbose,
    amount_col,
    balance_col,
    sender_col,
    net_account_name,
    out_dir,
    acct_filename,
    filename
):
    setup_logging(debug, verbose)

    data_filepath = get_latest_file(filename)
    logger.debug(f"Using {data_filepath} as data file")

    if acct_filename:
        acct_filepath = get_latest_file(
            acct_filename,
            glob_str="accounts_*.yml",
            date_extract_fct=lambda f: f.stem[9:]
        )
        logger.debug(f"Using {acct_filepath} as accounts file.")
        with open(acct_filepath) as acct_file:
            accounts = yaml.safe_load(acct_file)
    else:
        accounts = None

    v_book = ValidatedBook(accounts)

    with open(data_filepath) as data_file:
        v_book.add_entries_from_yaml(
            data_file, amount_col, balance_col, sender_col, net_account_name
        )

    out_path = Path(out_dir) / "04_valid_bookings"
    if not out_path.is_dir():
        out_path.mkdir(parents=True)
    v_book.to_file(out_path)


if __name__ == "__main__":
    validate()
