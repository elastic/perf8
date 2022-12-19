#
# Licensed to Elasticsearch B.V. under one or more contributor
# license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright
# ownership. Elasticsearch B.V. licenses this file to you under
# the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# 	http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
import sys
import asyncio
import argparse
import os
import logging

from perf8 import __version__
from perf8.plugins.base import get_registered_plugins
from perf8.watcher import WatchedProcess
from perf8.logger import set_logger


HERE = os.path.dirname(__file__)


def parser():
    aparser = argparse.ArgumentParser(
        description="Python Performance Tracking.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    for plugin in get_registered_plugins():
        aparser.add_argument(
            f"--{plugin.name}",
            action="store_true",
            default=False,
            help=plugin.description,
        )
        # XXX ask the plugin for its arguments and set them in a group

    aparser.add_argument(
        "-t",
        "--target-dir",
        default=os.path.join(os.getcwd(), "perf8-report"),
        type=str,
        help="target dir for results",
    )
    aparser.add_argument(
        "--title",
        default="Performance Report",
        type=str,
        help="String used for the report title",
    )
    aparser.add_argument(
        "-r",
        "--report",
        default="report.html",
        type=str,
        help="report file",
    )
    aparser.add_argument(
        "--refresh-rate",
        type=float,
        default=5.0,
        help="Refresh rate",
    )
    aparser.add_argument(
        "-c",
        "--command",
        default=os.path.join(HERE, "tests", "demo.py"),
        type=str,
        nargs=argparse.REMAINDER,
        help="Command to run",
    )

    aparser.add_argument(
        "--all",
        action="store_true",
        default=False,
        help="Use all plugins",
    )

    aparser.add_argument(
        "--version",
        action="store_true",
        default=False,
        help="Displays version and exits.",
    )

    aparser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help=(
            "Verbosity level. -v will display "
            "tracebacks. -vv requests and responses."
        ),
    )

    return aparser


def main(args=None):
    os.environ["PERF8_ARGS"] = "::".join(sys.argv[1:])

    if args is None:
        aparser = parser()
        args = aparser.parse_args()

    if args.version:
        print(__version__)
        sys.exit(0)

    if args.all:
        for plugin in get_registered_plugins():
            if plugin.name == "cprofile":
                args.cprofile = False
            else:
                setattr(args, plugin.name.replace("-", "_"), True)

    if args.memray and args.cprofile:
        raise Exception("You can't use --memray and --cprofile at the same time")

    if args.verbose > 0:
        set_logger(logging.DEBUG)
    else:
        set_logger(logging.INFO)

    asyncio.run(WatchedProcess(args).run())
    return 0


if __name__ == "__main__":
    main()
