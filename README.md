# stoier

stoier is the accounting helper toolkit.

## 00_csv_to_yaml

This script reads Postbank bank statements and converts rows into dictionaries

> Note: No deduplication of rows is done at this point!

### Example:

The following command will read all CSVs in `data/00_account`.
If the string _gebuchte Umsätze_ is encountered in the first column of a row, the data will start
2 rows after that. 
A custom header is used. 
Results will be written to the `dist` directory.

```zsh
$ 00_csv_to_yml -v dist -t "0:gebuchte Umsätze:2" data/00_account/*.csv -h "date_1:date_2:type:details:sender:receiver:amount:balance" -r
```

Options:
 -v: verbose output
 -d: debug output
 -t: trigger; split head from body
 -h: header; add a custom csv header
 -r: read file in reverse order
 dist: out directory

Alternatively you could use the following command to skip only 1 row after the trigger and use the
row after the trigger as header.

```zsh
$ 00_csv_to_yml -v dist -t "0:gebuchte Umsätze:1" data/00_account/*.csv 
```

## 01_clean

This script removes control characters from data.

> Note: `01_clean` will always select the latest file. 

```zsh
$ 01_clean -v dist dist/01_bookings
```

Options:
 -v: verbose output
 -d: debug output
 dist: out directory

## 02_deduplicate

Since this Postbank csv files have overlapping time slots, this scripts will deduplicate the records.
Its writes to files: One with the unique bookings, one with all the customes. The customer file needs to be enriched manually with the "virtual account" they belong to, in our case mostly the interal customer reference number.
> Note: `02_deduplicate` will always select the latest file. 

All bookings between _1.1.2020_ (incl.) and _31.12.2020_ (incl.) will be added to the result.

```zsh
$ 02_deduplicate -v dist dist/02_clean_bookings -s 01.01.2020 -e 31.12.2020
```

Options:
 -v: verbose output
 -d: debug output
 -s: start date
 -e: end date
 dist: out directory

## 03_validate

This scripts returns a file which contains a sorted list of bookings, grouped by day. Each booking has a field
 * `gross_accounts` (internal customer reference),
 * `ìd` (idetifier per day),
 * `net_accounts`
 * `vat`
 * `vat_account`

> Note: `03_validate` will always select the latest file. 

```zsh
$ 03_validate -d dist dist/03_unique_bookings
```
Options:
 -v: verbose output
 -d: debug output
 dist: out directory


## 07_afa

This tool can help you to calculate your afa.

Create a yaml-file for each item/group/pool with the following format.

```yaml
name: this_new_thing
description: The new black thing on the roof
date_of_purchase: 2019-01-23
price: 367.35
estimated_lifetime_years: 5
components:
  - name: Housing
    price: 154.23
  - name: Components
    price: 188.12
  - name: Paint
    price: 25.00
```

> Note: Only name, description, date_of_purchase, price and estimated_lifetime_years are required. The rest is optional an can be used by you to take notes about components, purchases etc.

By default it will give the values for last year (as you need the current years afa less frequent this is the default).

```zsh
$ 07_afa -v data/07_afa -y 2019
this_new_thing (The new black thing on the roof)
None: 73.470
Original price 367.350 (2019-01-23)
```

## Copyright

* Bootswatch Theme "vapor" by Thomas Park
* Bootstrap by Bootstrap Team 
* stoier by Florian Rämisch
