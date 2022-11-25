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

from perf8.util import get_plugin_klass, run_script


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
        "--plugins",
        type=str,
        default="",
        help="Plugins to use",
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

    plugins = [
        get_plugin_klass(fqn)(args)
        for fqn in args.plugins.split(",")
        if fqn.strip() != ""
    ]

    cmd_line = shlex.split(args.script[0])

    script = cmd_line[0]
    script_args = cmd_line[1:]

    for plugin in plugins:
        plugin.enable()
        # no in-process plugins, we just run it
        try:
            run_script(script, script_args)
        finally:
            for plugin in reversed(plugins):
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
    print(f"Wrote {report}")


if __name__ == "__main__":
    main()
