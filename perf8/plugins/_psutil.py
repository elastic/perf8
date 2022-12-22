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
import psutil

from perf8.plugins.base import BasePlugin, register_plugin


class ResourceWatcher(BasePlugin):
    name = "psutil"
    in_process = False
    description = "System metrics with psutil"
    priority = 0

    def __init__(self, args):
        super().__init__(args)
        self.report_fd = self.writer = self.proc_info = None
        self.report_file = os.path.join(args.target_dir, "report.csv")

    def start(self, pid):
        self.enabled = True
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
        try:
            info = self.proc_info.as_dict()
        except Exception as e:
            self.warning(f"Could not get info {e}")
            return

        self.debug("Probing")
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

        try:
            self.writer.writerow(metrics)
            self.report_fd.flush()
        except ValueError:
            self.warning(f"Failed to write in {self.report_file}")

    def stop(self, pid):
        self.enabled = False

        if self.report_fd is None:
            self.warning("No data collected for psutil")
            return []

        self.report_fd.close()

        def extract_memory(row):
            return round(int(row[0]) / (1024 * 1024), 2)

        def extract_cpu(row):
            return float(row[6])

        def extract_fds(row):
            return int(row[1])

        def extract_th(row):
            return int(row[2])

        def extract_ctx(row):
            return int(row[3])

        plot_file = self.generate_plot(
            self.report_file, extract_memory, "Memory Usage (RSS)", "Bytes", "rss.png"
        )
        cpu_plot_file = self.generate_plot(
            self.report_file, extract_cpu, "CPU%", "%", "cpu.png"
        )
        th_plot_file = self.generate_plot(
            self.report_file, extract_fds, "Threads", "ths", "threads.png"
        )
        fds_plot_file = self.generate_plot(
            self.report_file, extract_th, "File Descriptors", "FDs", "fds.png"
        )
        ctx_plot_file = self.generate_plot(
            self.report_file, extract_ctx, "Context Switches", "ctx", "ctx.png"
        )

        return [
            {"label": "Memory Usage", "file": plot_file, "type": "image"},
            {"label": "CPU Usage", "file": cpu_plot_file, "type": "image"},
            {"label": "Threads", "file": th_plot_file, "type": "image"},
            {"label": "FDs", "file": fds_plot_file, "type": "image"},
            {"label": "Context Switch", "file": ctx_plot_file, "type": "image"},
            {"label": "psutil CSV data", "file": self.report_file, "type": "artifact"},
        ]


register_plugin(ResourceWatcher)
