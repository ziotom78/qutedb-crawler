#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

"""
QuteDB crawler: scan a folder of Qubic test files and creates thumbnails and metadata
"""

__version__ = "0.1.0"

import json
from pathlib import Path
from datetime import datetime
import logging as log
import subprocess
import tempfile
from argparse import ArgumentParser

import matplotlib

matplotlib.use("Agg")
from astropy.io import fits

import matplotlib.pylab as plt
from qubicpack.qubicfp import qubicfp
import numpy as np

qubicfp.verbosity = 0  # Force qubicfp not to write messages on the screen

default_tmp_dir = Path(tempfile._get_default_tempdir())
LOG_LEVELS = {
    "critical": log.CRITICAL,
    "error": log.ERROR,
    "info": log.INFO,
    "warning": log.WARNING,
    "debug": log.DEBUG,
}
THUMBNAIL_FILE_NAME = "quicklook_plot.png"


def create_plot(testpath, always_make=False):
    filename = testpath / THUMBNAIL_FILE_NAME
    if (not always_make) and filename.exists():
        log.debug(
            'File "%s" already exist for test "%s", so no need to re-create it',
            THUMBNAIL_FILE_NAME,
            str(testpath),
        )
        return filename

    try:
        a = qubicfp()
        a.read_qubicstudio_dataset(str(testpath))
        a.quicklook(xwin=False, filename=filename)
    except:
        log.error('Unable to create plot for test "%s"', str(testpath))
        # Do not bother complaining too much, just keep things going
        return None

    try:
        # Optimize the size of the PNG file
        temp_name = next(tempfile._get_candidate_names())
        full_temp_name = str(default_tmp_dir / temp_name)
        subprocess.run(["pngquant", "-f", "--output", full_temp_name, "32", filename])
        subprocess.run(["optipng", full_temp_name])
        subprocess.run(["mv", "-f", full_temp_name, filename])
        log.debug(
            'Plot for test in "%s" has been compressed successfully', str(testpath)
        )
    except CalledProcessError:
        log.warn('Unable to compress "%s", leaving it uncompressed', filename)
        pass  # Ignore the error, we'll live with an uncompressed plot!

    return filename


def create_json(testpath, filename="metadata.json", always_make=False):
    json_filename = testpath / filename
    if (not always_make) and json_filename.exists():
        log.debug(
            'File "%s" already exist for test "%s", so no need to re-create it',
            filename,
            str(testpath),
        )
        return json_filename

    sum_path = testpath / "Sums"
    if (not sum_path.exists()) or (not sum_path.is_dir()):
        log.debug('Test "%s" does not contain scientific files', str(testpath))
        return None

    start_tstamp, end_tstamp = None, None

    # This is used to pick the first and last element in an array
    sample_mask = np.array([0, -1], dtype="int")
    for curfile in sum_path.glob("science-asic*.fits"):
        with fits.open(curfile) as fp:
            cur_start_tstamp, cur_end_tstamp = 1.0e-3 * fp[1].data.field(0)[sample_mask]

        if (not start_tstamp) or (cur_start_tstamp < start_tstamp):
            start_tstamp = cur_start_tstamp

        if (not end_tstamp) or (cur_end_tstamp > end_tstamp):
            end_tstamp = cur_end_tstamp

    if (not start_tstamp) or (not end_tstamp):
        log.warn(
            'No scientific files found for test "%s", skipping creation of "%s"',
            str(testpath),
            filename,
        )
        return None

    startobs, endobs = [
        datetime.utcfromtimestamp(x) for x in (start_tstamp, end_tstamp)
    ]
    strftime_mask = "%Y-%m-%d %H:%M:%S"
    metadata = {
        "start_time": startobs.strftime(strftime_mask),
        "end_time": endobs.strftime(strftime_mask),
        "duration_s": (endobs - startobs).seconds,
    }

    with json_filename.open(mode="wt") as fp:
        json.dump(metadata, fp, indent=4, sort_keys=True)
    log.debug('Metadata have been saved in "%s"', str(json_filename))

    return json_filename


def process_folders(rootpath: str, always_make=False):
    if not type(rootpath) == type(Path):
        curpath = Path(rootpath)
    else:
        curpath = rootpath

    for curentry in curpath.glob("*"):
        if not curentry.is_dir():
            continue

        if curentry.match("????-??-??_??.??.??__*"):
            log.info('Processing test "%s"', str(curentry))
            create_plot(testpath=curentry, always_make=always_make)
            create_json(curentry, always_make=always_make)
        else:
            log.debug('Entering directory "%s"', str(curentry))
            # Recursive call
            process_folders(rootpath=curentry)


def main():
    parser = ArgumentParser(
        description="Crawl a folder containing Qubic test files and create thumbnails"
    )
    parser.add_argument(
        "folder",
        metavar="PATH",
        type=str,
        help="Path of the folder containing the test files",
    )
    parser.add_argument(
        "--always-make",
        "-b",
        default=False,
        action="store_true",
        help="""
Always create plots and JSON files. (The default is to check if they already
exist, and skip their creation if it is so.)
        """,
    )
    parser.add_argument(
        "--log-level",
        default="info",
        help=f"""
Set the log level. Possible values are {', '.join(LOG_LEVELS.keys())}.
""",
    )

    args = parser.parse_args()

    log.basicConfig(
        format="[%(asctime)s] %(levelname)s - %(message)s",
        level=LOG_LEVELS[args.log_level],
    )
    process_folders(rootpath=args.folder, always_make=args.always_make)


if __name__ == "__main__":
    main()
