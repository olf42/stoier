#!/usr/bin/env python3

import click
import logging
import yaml

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from stoier.log import setup_logging

logger = logging.getLogger(__name__)


ROUND = 3


class AfaYearError(Exception):
    pass


class Afa:

    def __init__(
        self,
        name,
        description,
        price,
        date_of_purchase,
        estimated_lifetime
    ):
        self.name = name
        self.description = description
        self.price = price
        self.date_of_purchase = date_of_purchase
        self.estimated_lifetime = estimated_lifetime

    @classmethod
    def from_yaml(cls, yaml_file):
        data = yaml.safe_load(yaml_file)
        return cls(
            data["name"],
            data["description"],
            Decimal(data["price"]),
            data["date_of_purchase"],
            data["estimated_lifetime_years"]
        )

    def get_afa_value(self, year=None):
        """Returns the afa for last year (default) or any other year."""
        if year is None:
            year = datetime.now().year - 1

        logger.debug(f"Getting afa for {self.name} in {year}.")
        month_of_purchase = self.date_of_purchase.month
        months_1st_year = 12 - month_of_purchase + 1
        months_last_year = 12 - months_1st_year
        if year < self.date_of_purchase.year:
            raise AfaYearError(
                f"{self.name} was not purchased yet."
            )
        if (year - self.date_of_purchase.year) == 0:  # first year
            return round(
                Decimal(months_1st_year / (12 * self.estimated_lifetime)) * self.price,
                ROUND
            )
        elif (year - self.date_of_purchase.year) <= self.estimated_lifetime:  # year in lifetime
            return round(self.price / self.estimated_lifetime, ROUND)
        elif (year - self.date_of_purchase.year) == self.estimated_lifetime + 1:  # last year
            return round(
                Decimal(months_last_year / (12 * self.estimated_lifetime)) * self.price,
                ROUND
            )
        else:  # after end of lifetime
            return Decimal("0.0")

    def get_afa(self, year):
        return (
            self.name,
            self.description,
            round(self.price, ROUND),
            self.date_of_purchase,
            self.estimated_lifetime,
            self.get_afa_value(year)
        )


@click.command()
@click.option("-d", "--debug", is_flag=True, default=False)
@click.option("-v", "--verbose", is_flag=True, default=False)
@click.option("-y", "--year", "year", type=int, default=None)
@click.argument("afa_dir", type=Path)
def afa_helper(
    debug,
    verbose,
    year,
    afa_dir
):
    setup_logging(debug, verbose)

    logger.debug(f"Using files from {afa_dir} as data source.")
    for filepath in afa_dir.glob("*.yaml"):
        with open(filepath) as data_file:
            afa = Afa.from_yaml(data_file)
        try:
            name, description, price, dop, el, value = afa.get_afa(year)
        except AfaYearError as e:
            logger.info(f"{e}\nSkipping.\n")
            continue
        print(f"{name} ({description})")
        print(f"{year}: {value}")
        print(f"Original price {price} ({dop})\n")


if __name__ == "__main__":
    afa_helper()
