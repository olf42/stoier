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
$ 00_csv_to_yml -v dist -t "0:gebuchte Umsätze:2" data/00_account/*.csv -h "date_1:date_2:type:details:sender:receiver:amount:balance" 
```

Alternatively you could use the following command to skip only 1 row after the trigger and use the
row after the trigger as header.

```zsh
$ 00_csv_to_yml -v dist -t "0:gebuchte Umsätze:1" data/00_account/*.csv 
```

## 01_clean

> Note: `01_clean` will always select the latest file. 

```zsh
$ 01_clean -v dist dist/01_bookings
```

## 02_deduplicate

> Note: `02_deduplicate` will always select the latest file. 

All bookings between _1.1.2020_ (incl.) and _31.12.2020_ (incl.) will be added to the result.

```zsh
$ 02_deduplicate -v dist dist/02_clean_bookings -s 01.01.2020 -e 31.12.2020
```

## 03_validate

> Note: `03_deduplicate` will always select the latest file. 

```zsh
$ 03_validate -d dist dist/03_unique_bookings
```
