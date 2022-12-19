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
"""
Wrapper script
"""
import os
import argparse
import json
import shlex
import sys
from copy import copy
import runpy
import pathlib
import signal
import logging

from perf8.logger import logger, set_logger
from perf8.plugins.base import get_plugin_klass, set_plugins


def run_script(script_file, script_args):
    saved = copy(sys.argv[:])
    sys.path[0] = str(pathlib.Path(script_file).resolve().parent.absolute())
    sys.argv[:] = [script_file, *script_args]
    runpy.run_path(script_file, run_name="__main__")
    sys.argv[:] = saved


def main():
    parser = argparse.ArgumentParser(
        description="Perf8 Wrapper",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-t",
        "--target-dir",
        default=os.getcwd(),
        type=str,
        help="target dir for results",
    )
    parser.add_argument(
        "--ppid",
        type=int,
        help="Parent process id",
    )
    parser.add_argument(
        "--plugins",
        type=str,
        default="",
        help="Plugins to use",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help=(
            "Verbosity level. -v will display "
            "tracebacks. -vv requests and responses."
        ),
    )
    parser.add_argument(
        "-r",
        "--report",
        default="report.json",
        type=str,
        help="report file",
    )
    parser.add_argument(
        "-s",
        "--script",
        default="dummy.py --with-option -a=2",
        type=str,
        nargs=argparse.REMAINDER,
        help="Python script to run",
    )

    # XXX pass-through perf8 args so the plugins can pick there options
    args = parser.parse_args()

    if args.verbose > 0:
        set_logger(logging.DEBUG)
    else:
        set_logger(logging.INFO)

    args.target_dir = os.path.abspath(args.target_dir)
    os.makedirs(args.target_dir, exist_ok=True)

    plugins = [
        get_plugin_klass(fqn)(args)
        for fqn in args.plugins.split(",")
        if fqn.strip() != ""
    ]

    plugins.sort(key=lambda x: -x.priority)
    set_plugins(plugins)

    cmd_line = shlex.split(args.script[0])

    script = cmd_line[0]
    script_args = cmd_line[1:]

    os.environ["PERF8"] = "1"
    async_plugins = []

    for plugin in plugins:
        # async plugins are activated inside the target app
        if not plugin.is_async:
            plugin.enable()
        else:
            async_plugins.append(plugin.name)

    os.environ["PERF8_ASYNC_PLUGIN"] = ",".join(async_plugins)
    os.environ["PERF8"] = "1"

    # we disable plugins right away on SIGTERM / SIGINT
    def _exit(signum, frame):
        for plugin in reversed(plugins):
            if not plugin.is_async and plugin.in_process:
                plugin.disable()
        # re-raise interrupt
        raise SystemExit()

    signal.signal(signal.SIGINT, _exit)
    signal.signal(signal.SIGTERM, _exit)

    # no in-process plugins, we just run it
    try:
        run_script(script, script_args)
    finally:
        logger.info(f"Script is over -- sending a signal to {args.ppid}")
        # script is over, send a signal to the parent
        os.kill(args.ppid, signal.SIGUSR1)

        for plugin in reversed(plugins):
            if not plugin.is_async and plugin.in_process:
                plugin.disable()

        # sending back the reports to the main process through json
        reports = []
        for plugin in plugins:
            for report in plugin.report():
                report["name"] = plugin.name
                reports.append(report)

        report = os.path.join(args.target_dir, args.report)
        with open(report, "w") as f:
            f.write(json.dumps({"reports": reports}))
        logger.info(f"Wrote {report}")


if __name__ == "__main__":
    main()
