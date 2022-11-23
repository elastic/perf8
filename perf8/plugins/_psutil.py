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
import csv
import time
import os

import matplotlib.pyplot as plt
import psutil

from perf8.util import register_plugin


class ResourceWatcher:
    name = "psutil"
    fqn = f"{__module__}:{__qualname__}"
    in_process = False
    description = "System metrics with psutil"

    def __init__(self, args):
        self.target_dir = args.target_dir
        self.report_fd = self.writer = self.proc_info = None
        self.report_file = os.path.join(args.target_dir, "report.csv")

    def generate_plot(self, path):
        x = []
        rss = []
        # cpu = []

        with open(path) as csvfile:
            lines = csv.reader(csvfile, delimiter=",")
            for i, row in enumerate(lines):
                if i == 0:
                    continue
                x.append(row[-1])
                bytes = round(int(row[0]) / (1024 * 1024), 2)
                rss.append(bytes)  # rss
                # cpu.append(row[-1])

        # plt.plot(x, cpu, color="r", linestyle="dashed", marker="o", label="CPU %")
        plt.plot(x, rss, color="g", linestyle="dashed", marker="o", label="RSS")

        plt.xticks(rotation=25)
        plt.xlabel("Duration")
        plt.ylabel("Bytes")  # switch to KiB or MiB automatically - XXX
        plt.title("Performance Report", fontsize=20)
        plt.grid()
        plt.legend()
        plot_file = os.path.join(self.target_dir, "report.png")
        plt.savefig(plot_file)
        return plot_file

    def start(self, pid):
        self.proc_info = psutil.Process(pid)
        self.report_fd = open(self.report_file, "w")
        self.writer = csv.writer(self.report_fd)
        self.started_at = time.time()
        self.rows = (
            "rss",
            "num_fds",
            "num_threads",
            "ctx_switch",
            "cpu_user",
            "cpu_system",
            "cpu_percent",
            "when",
            "since",
        )
        # headers
        self.writer.writerow(self.rows)

    async def probe(self, pid):
        info = self.proc_info.as_dict()
        probed_at = time.time()
        metrics = (
            info["memory_info"].rss,
            info["num_fds"],
            info["num_threads"],
            info["num_ctx_switches"].voluntary,
            info["cpu_times"].user,
            info["cpu_times"].system,
            info["cpu_percent"],
            probed_at,
            int(probed_at - self.started_at),
        )

        self.writer.writerow(metrics)
        self.report_fd.flush()

    def stop(self, pid):
        if self.report_fd is None:
            return []

        self.report_fd.close()
        plot_file = self.generate_plot(self.report_file)
        return [
            {"label": "psutil memory report", "file": plot_file, "type": "image"},
            {"label": "psutil csv data", "file": self.report_file, "type": "artifact"},
        ]


register_plugin(ResourceWatcher)
