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
import json
import datetime
from collections import defaultdict
import base64
import mimetypes

from jinja2 import Environment, FileSystemLoader
from perf8 import __version__
from perf8.logger import logger


HERE = os.path.dirname(__file__)


class Reporter:
    def __init__(self, args):
        self.environment = Environment(
            loader=FileSystemLoader(os.path.join(HERE, "templates"))
        )
        self.args = args

    def render(self, name, **args):
        template = self.environment.get_template(name)
        args["args"] = self.args
        args["version"] = __version__
        args["created_at"] = datetime.datetime.now().strftime("%d-%m-%y %H:%M:%S")
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
            default_page="summary.html",
            reports=all_reports,
            plugins=plugins,
        )

        # summary
        self.render("summary.html", plugins=plugins)

        return html_report
