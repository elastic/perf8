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

from perf8 import __version__


HERE = os.path.dirname(__file__)
MENU_TEMPLATE = os.path.join(HERE, "templates", "menu.html.tmpl")
INDEX_TEMPLATE = os.path.join(HERE, "templates", "index.html.tmpl")
SUMMARY_TEMPLATE = os.path.join(HERE, "templates", "summary.html.tmpl")


def generate_report(run_summary, out_reports, plugins, args):
    reports = defaultdict(list)
    reports.update(out_reports)

    # read report.json to extend the list
    with open(run_summary) as f:
        data = json.loads(f.read())

        for report in data["reports"]:
            reports[report["name"]].append(report)

    print("[perf8] Reports generated:")
    for plugin in plugins:
        if plugin.name not in reports:
            continue
        print(
            f"[perf8] Plugin {plugin.name} generated {len(reports[plugin.name])} report(s)"
        )

    # generating menu
    with open(MENU_TEMPLATE) as f:
        render = f.read()

    html_reports = []
    artifacts = []

    for reporter in reports.values():
        for report in reporter:
            relative = os.path.basename(report["file"])
            if report["type"] == "artifact":
                artifacts.append(
                    f"<li><a href='{relative}' download='{relative}' target='_blank'>{report['label']}</a></li>"
                )

                continue

            html_reports.append(
                f"<li><a href='{relative}' target='content'>{report['label']}</a></li>"
            )

    html_report = os.path.join(args.target_dir, "menu.html")
    with open(html_report, "w") as f:
        f.write(
            render
            % {
                "reports": "\n".join(html_reports),
                "artifacts": "\n".join(artifacts),
                "version": __version__,
                "created_at": datetime.datetime.now().strftime("%d-%m-%y %H:%M:%S"),
                "title": args.title,
            }
        )

    with open(INDEX_TEMPLATE) as f:
        render = f.read()
    html_report = os.path.join(args.target_dir, "index.html")
    with open(html_report, "w") as f:
        f.write(render % {"default_page": "summary.html", "title": args.title})

    # summary
    plugins = [f"<li>{plugin.name} -- {plugin.description}</li>" for plugin in plugins]
    with open(SUMMARY_TEMPLATE) as f:
        render = f.read()
    summary_page = os.path.join(args.target_dir, "summary.html")
    with open(summary_page, "w") as f:
        f.write(
            render
            % {
                "command": " ".join(args.command),
                "title": args.title,
                "plugins": "\n".join(plugins),
            }
        )
    return html_report
