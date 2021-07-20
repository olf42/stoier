#!/usr/bin/env python3

import click
import http.server
import logging
import shutil
import socketserver
import yaml

from collections import OrderedDict, defaultdict
from datetime import datetime
from pathlib import Path
from stoier.log import setup_logging
from stoier.utils import iterate_dated_dict, get_latest_file, render_html


logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"
PORT = 8000


class Report():

    templates_path = Path(__file__).parent / "templates"
    templates = {
        "account": templates_path / "account.html"
    }

    def __init__(self):
        self.entries = OrderedDict()
        self.accounts = dict()
        self.invoices = defaultdict(list)

    def sort_accounts(self):
        self.accounts = OrderedDict(sorted(self.accounts.items()))

    def add_entries_from_yaml(self, yaml_file):
        data = yaml.load(yaml_file, Loader=yaml.Loader)
        dates = [datetime.strptime(date, "%Y-%m-%d") for date in data.keys()]
        dates.sort()
        for date, e, entry in iterate_dated_dict(data):
            if date not in self.entries.keys():
                self.entries[date] = []
            self.entries[date].append(entry)

    def add_account_from_yaml(self, yaml_file, account_name):
        account_data = yaml.load(yaml_file, Loader=yaml.Loader)
        self.accounts[account_name] = account_data

    def add_invoice(self, account, invoice_file):
        invoice = yaml.load(invoice_file, Loader=yaml.Loader)
        self.invoices[account].append(invoice)

    def get_account_context(self, account_name):
        logger.debug(f"Get context for account {account_name}")
        accounts = list(self.accounts.keys())
        try:
            previous_account = accounts[accounts.index(account_name)-1] + ".html"
        except Exception:
            previous_account = "#"
        try:
            next_account = accounts[accounts.index(account_name)+1] + ".html"
        except Exception:
            next_account = "#"
        context = {
            "previous": previous_account,
            "next": next_account,
            "account_name": account_name,
            "bookings": self.accounts[account_name],
            "invoices": self.invoices[account_name]
        }
        return context

    def to_files(self, out_path):
        self.sort_accounts()
        for name, account in self.accounts.items():
            logging.info(f"Rendering account {name}")
            render_html(
                self.get_account_context(name),
                self.templates["account"],
                out_path / f"{name}.html"
            )

    @classmethod
    def from_dirs(cls, bookings_dir, accounts_dir, invoices_path=None):
        report = cls()

        bookings_path = get_latest_file(bookings_dir)
        logger.debug(f"Using {bookings_path} for bookings")
        with open(bookings_path) as yaml_file:
            report.add_entries_from_yaml(yaml_file)

        accounts_path = get_latest_file(
            accounts_dir, glob_str="*", ext="", date_extract_fct=lambda f: f.name)
        logger.debug(f"Using {accounts_path} for accounts")
        for account_filepath in Path(accounts_path).glob("*.yml"):
            logger.debug(f"Reading {account_filepath}")
            with open(account_filepath) as account_file:
                account_name = account_filepath.stem.split("_")[0]
                logger.info(f"Add account {account_name}")
                report.add_account_from_yaml(account_file, account_name)

        if invoices_path:
            logger.debug(f"Using {invoices_path} for invoices")
            for customer_dir in invoices_path.glob("*"):
                for invoice_path in customer_dir.glob("*.yaml"):
                    logger.info(f"Adding invoice {invoice_path.name}")
                    with open(invoice_path) as invoice_file:
                        report.add_invoice(customer_dir.name, invoice_file)
        return report


@click.command()
@click.option("-d", "--debug", is_flag=True, default=False)
@click.option("-v", "--verbose", is_flag=True, default=False)
@click.option("-p", "--port", default=PORT)
@click.option("--serve", "serve", is_flag=True, default=False)
@click.option("--invoices_dir", "invoices_path", default=None, type=Path)
@click.argument("out_dir")
@click.argument("bookings_dir")
@click.argument("accounts_dir")
def report(
    debug, verbose, port, serve, out_dir, invoices_path, bookings_dir, accounts_dir,
):
    setup_logging(debug, verbose)

    report = Report.from_dirs(bookings_dir, accounts_dir, invoices_path)

    now = datetime.now()
    out_path = Path(out_dir) / "06_report" / now.isoformat()
    if not out_path.is_dir():
        out_path.mkdir(parents=True)
    report.to_files(out_path)

    logger.debug("Copying static files")
    static_path = out_path / "static"
    static_path.mkdir()
    for static_file in STATIC_DIR.glob("*"):
        logger.debug(f"Copying {static_file}")
        shutil.copy(static_file, static_path / static_file.name)

    logger.info(f"Report written to {out_path}")

    if serve:
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=out_path, **kwargs)

        with socketserver.TCPServer(("", port), Handler) as httpd:
            logging.info(f"Serving at http://localhost:{port}/")
            httpd.serve_forever()


if __name__ == "__main__":
    report()
