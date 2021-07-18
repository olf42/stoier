import datetime
import logging
import yaml

logger = logging.getLogger(__name__)


def save_yaml(obj, out_path):
    now = datetime.datetime.now()
    outfilename = out_path / f"{now.isoformat()}.yml"
    with open(outfilename, "w") as outfile:
        yaml.safe_dump(obj, outfile)
    logger.info(f"Written {len(obj)} to file {outfilename}")


def get_date(date_str, date_format):
    if date_str:
        return datetime.datetime.strptime(date_str, date_format)
    else:
        return None
