import logging
import yaml

from datetime import datetime
from jinja2 import Template
from pathlib import Path

logger = logging.getLogger(__name__)


def save_yaml(obj, out_path, prefix="", date=None):
    if not date:
        date = datetime.now()
    outfilename = out_path / f"{prefix}{date.isoformat()}.yml"
    with open(outfilename, "w") as outfile:
        yaml.dump(obj, outfile)
    logger.info(f"Written {len(obj)} items to file {outfilename}")


def get_date(date_str, date_format):
    if date_str:
        return datetime.strptime(date_str, date_format)
    else:
        return None


def get_latest_file(
        filepath, glob_str="*.yml", ext=".yml", date_extract_fct=lambda f: f.stem
):
    """
    Given the input from (supposedly) a commandline argument this function returns
    the path to the latest file in the directory.

    Note: The latest file is the file with the latest isoformat date in the filename.

    If a filename is given, the filename is returned.

    This also works for directories. In that case, ext should be "".

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
        return filepath / f"{maxdate.isoformat()}{ext}"


def iterate_dated_dict(obj, *, date_format="%Y-%m-%d", start=None):
    dates = [datetime.strptime(date, date_format) for date in obj.keys()]
    dates.sort()
    if start:
        if start in dates:
            start_index = dates.index(start)
        else:
            for start_index, date in enumerate(dates):
                if date > start:
                    break
    else:
        start_index = 0
    for date in dates[start_index:]:
        date_str = date.strftime(date_format)
        date_entries = obj[date_str]
        for e, entry in enumerate(date_entries):
            yield date_str, e, entry


def render_html(context, template_filepath, out_filepath):
    with open(template_filepath) as infile:
        template = Template(infile.read())
    html = template.render(**context)
    with open(out_filepath, "w") as outfile:
        outfile.write(html)
