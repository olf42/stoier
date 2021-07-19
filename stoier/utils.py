import logging
import yaml

from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def save_yaml(obj, out_path):
    now = datetime.now()
    outfilename = out_path / f"{now.isoformat()}.yml"
    with open(outfilename, "w") as outfile:
        yaml.dump(obj, outfile)
    logger.info(f"Written {len(obj)} items to file {outfilename}")


def get_date(date_str, date_format):
    if date_str:
        return datetime.strptime(date_str, date_format)
    else:
        return None


def get_latest_file(filepath, glob_str="*.yml", date_extract_fct=lambda f: f.stem):
    """
    Given the input from (supposedly) a commandline argument this function returns
    the path to the latest file in the directory.

    Note: The latest file is the file with the latest isoformat date in the filename.

    If a filename is given, the filename is returned.

    :param filename: str/path of the dir or file
    :param glob_str: glob to be used to identify valid files. Default: *.yml
    :param date_extract_fct: callable, which is given the filename, which shall return
                             a datetime object.
    """
    if not isinstance(filepath, Path):
        filepath = Path(filepath)
    if filepath.is_file():
        return filepath
    else:
        logger.debug(f"Finding latest file in {filepath}")
        maxdate = None
        for fileindir in filepath.glob(glob_str):
            logger.debug(f"Checking {fileindir}")
            try:
                filedate = datetime.fromisoformat(date_extract_fct(fileindir))
            except Exception:
                continue
            if not maxdate:
                maxdate = filedate
                continue
            if filedate > maxdate:
                maxdate = filedate
                logger.debug(f"Setting {fileindir} as latest file.")
        return filepath / f"{maxdate.isoformat()}.yml"
