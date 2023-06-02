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
import os
import csv
import json
import datetime
from collections import defaultdict
import base64
import mimetypes
import platform
import psutil
import humanize

from jinja2 import Environment, FileSystemLoader
from perf8 import __version__
from perf8.logger import logger
from perf8.plot import Graph, Line
from matplotlib.colors import BASE_COLORS


HERE = os.path.dirname(__file__)

# cgroup v1 file
docker_memlimit = "/sys/fs/cgroup/memory/memory.limit_in_bytes"

# cgroup v2 file
docker_memlimit_v2 = "/sys/fs/cgroup/memory.max"

if os.path.exists(docker_memlimit):
    with open(docker_memlimit) as f:
        system_memory = int(f.read().strip())
elif os.path.exists(docker_memlimit_v2):
    with open(docker_memlimit_v2) as f:
        system_memory = int(f.read().strip())
else:
    system_memory = psutil.virtual_memory().total


class Datafile:
    def __init__(self, report_file, fields):
        self.report_file = report_file
        self.rows = fields
        self.writer = None
        self.count = 0

    def open(self):
        self.report_fd = open(self.report_file, "w")
        self.writer = csv.writer(self.report_fd)
        self.writer.writerow(self.rows)

    def add(self, values):
        try:
            self.writer.writerow(values)
            self.report_fd.flush()
        except ValueError:
            logger.warning(f"Failed to write in {self.report_file}")
        self.count += 1

    def close(self):
        self.report_fd.close()


class Reporter:
    def __init__(self, args, execution_info, statsd_data):
        self.environment = Environment(
            loader=FileSystemLoader(os.path.join(HERE, "templates"))
        )
        self.args = args
        self.execution_info = execution_info
        if args.max_duration == 0:
            self.overtime = False
        else:
            self.overtime = self.execution_info["duration_s"] > args.max_duration
        self.successes = 0
        self.failures = self.overtime and 1 or 0
        self.statsd_data = statsd_data

    @property
    def success(self):
        return self.failures == 0 and self.successes > 0

    def get_arguments(self):
        return vars(self.args)

    def get_system_info(self):
        # cpu_freq is broken on M1 see https://github.com/giampaolo/psutil/issues/1892
        # until this is resolved we can just ignore that info
        try:
            freq = f"{psutil.cpu_freq(percpu=False).current} Hz"
        except (FileNotFoundError, AttributeError):
            logger.warning("Could not get the CPU frequency")
            freq = "N/A"

        return {
            "OS Name": platform.system(),
            "Architecture": platform.architecture()[0],
            "Machine Type": platform.uname().machine,
            "Network Name": platform.uname().node,
            "Python Version": platform.python_version(),
            "Physical Memory": humanize.naturalsize(system_memory, binary=True),
            "Number of Cores": psutil.cpu_count(),
            "CPU Frequency": freq,
        }

    def render(self, name, **args):
        template = self.environment.get_template(name)
        args["args"] = self.args
        args["version"] = __version__
        args["created_at"] = datetime.datetime.now().strftime("%d-%m-%y %H:%M:%S")
        args["success"] = self.success
        args["failures"] = self.failures
        args["successes"] = self.successes
        args["total"] = self.failures + self.successes
        if self.args.description is None:
            desc = ""
        elif os.path.exists(self.args.description):
            with open(self.args.description) as f:
                desc = f.read().strip()
        else:
            desc = self.args.description
        args["description"] = desc

        content = template.render(**args)
        target = os.path.join(self.args.target_dir, name)
        with open(target, "w") as f:
            f.write(content)
        return target

    def generate(self, run_summary, out_reports, plugins):
        reports = defaultdict(list)
        reports.update(out_reports)

        # read report.json to extend the list
        with open(run_summary) as f:
            data = json.loads(f.read())

            for report in data["reports"]:
                reports[report["name"]].append(report)

        logger.info("Reports generated:")
        for plugin in plugins:
            if plugin.name not in reports:
                continue
            logger.info(
                f"Plugin {plugin.name} generated {len(reports[plugin.name])} report(s)"
            )

        # generating index page
        if self.args.max_duration > 0:
            if self.overtime:
                result = (
                    False,
                    f"Took over {humanize.precisedelta(self.args.max_duration)}",
                )
            else:
                result = True, "Fast and Crisp"
            all_reports = [
                {"num": 0, "result": result, "type": "result", "name": "general"}
            ]
            num = 1
        else:
            all_reports = []
            num = 0

        for item in reports.values():
            for report in item:
                report["num"] = num
                report["id"] = f"report-{num}"
                num += 1
                if report["type"] == "html":
                    with open(report["file"]) as f:
                        report["html"] = html = f.read()
                        report["html_b64"] = base64.b64encode(
                            html.encode("utf8")
                        ).decode("utf-8")
                elif report["type"] == "image":
                    with open(report["file"], "rb") as f:
                        data = base64.b64encode(f.read()).decode("utf-8")
                        report["image"] = data
                        report["mimetype"] = mimetypes.guess_type(report["file"])[0]
                elif report["type"] == "artifact":
                    report["file_size"] = humanize.naturalsize(
                        os.stat(report["file"]).st_size, binary=True
                    )
                elif report["type"] == "result":
                    if report["result"][0]:
                        self.successes += 1
                    else:
                        self.failures += 1
                all_reports.append(report)

        # if we got stuff from statsd, we create one report per statsd type
        if self.statsd_data is not None:
            by_dates = []
            counter_keys = []

            for series in self.statsd_data.get_series():
                by_date = {}
                for key, value in series["counters"].items():
                    if key not in counter_keys:
                        counter_keys.append(key)
                    by_date[key] = value

                by_dates.append((series["when"], by_date))

            lines = []
            colors = list(BASE_COLORS.keys())

            for i, key in enumerate(counter_keys):
                samples = []
                for y, (when, data) in enumerate(by_dates):
                    samples.append((when, data.get(key, 0)))
                lines.append(Line(samples, key, None, colors[i]))

            graph = Graph(
                "Statsd Counters",
                self.args.target_dir,
                "statsd.png",
                "count",
                None,
                *lines,
            )

            report = {
                "type": "image",
                "file": graph.generate(logger),
                "label": "Statsd Counters",
            }
            report["num"] = num
            report["id"] = f"report-{num}"
            num += 1

            with open(report["file"], "rb") as f:
                data = base64.b64encode(f.read()).decode("utf-8")
                report["image"] = data
                report["mimetype"] = mimetypes.guess_type(report["file"])[0]

            all_reports.append(report)

        def _s(report):
            if report["type"] == "artifact":
                suffix = "2"
            elif report["type"] == "image":
                suffix = "1"
            else:
                suffix = "0"

            return int(f'{suffix}{report["num"]}')

        all_reports.sort(key=_s)
        html_report = self.render(
            "index.html",
            reports=all_reports,
            plugins=plugins,
            system_info=self.get_system_info(),
            arguments=self.get_arguments(),
            execution_info=self.execution_info,
        )

        return html_report
