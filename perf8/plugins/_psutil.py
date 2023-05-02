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
import humanize
import tempfile

import matplotlib.ticker as tkr
from perf8.plugins.base import BasePlugin, register_plugin


def scantree(path):
    try:
        for entry in os.scandir(path):
            if entry.is_dir(follow_symlinks=False):
                yield from scantree(entry.path)
            else:
                if not entry.name.startswith("."):
                    yield entry
    except PermissionError:
        pass


# XXX expensive
def disk_usage(path):
    size = 0
    for entry in scantree(path):
        try:
            size += entry.stat().st_size
        except (OSError, PermissionError, FileNotFoundError):
            pass
    return size


def to_rss_bytes(data):
    data = str(data)
    if data.endswith("G"):
        return int(data[:-1]) * 1024 * 1024 * 1024
    elif data.endswith("M"):
        return int(data[:-1]) * 1024 * 1024
    elif data.endswith("K"):
        return int(data[:-1]) * 1024
    else:
        return int(data)


class ResourceWatcher(BasePlugin):
    name = "psutil"
    in_process = False
    description = "System metrics with psutil"
    priority = 0
    arguments = [
        ("max-rss", {"type": str, "default": "0", "help": "Maximum allowed RSS"}),
        (
            "disk-path",
            {"type": str, "default": tempfile.gettempdir(), "help": "Path to watch"},
        ),
    ]

    def __init__(self, args):
        super().__init__(args)
        self.max_allowed_rss = to_rss_bytes(args.psutil_max_rss)
        self.report_fd = self.writer = self.proc_info = None
        self.report_file = os.path.join(args.target_dir, "report.csv")
        self.path = args.psutil_disk_path

    def _start(self, pid):
        self.proc_info = psutil.Process(pid)
        self.report_fd = open(self.report_file, "w")
        self.writer = csv.writer(self.report_fd)
        self.started_at = time.time()
        self.initial_disk_usage = disk_usage(self.path)

        self.rows = (
            "disk_usage",
            "disk_io_read_count",
            "disk_io_write_count",
            "disk_io_read_bytes",
            "disk_io_write_bytes",
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
        self.max_rss = 0

    async def probe(self, pid):
        try:
            info = self.proc_info.as_dict()
        except Exception as e:
            self.warning(f"Could not get info {e}")
            return

        self.debug("Probing")
        probed_at = time.time()
        current_rss = info["memory_info"].rss
        if current_rss > self.max_rss:
            self.max_rss = current_rss

        disk_io = psutil.disk_io_counters()

        metrics = (
            disk_usage(self.path) - self.initial_disk_usage,
            disk_io.read_count,
            disk_io.write_count,
            disk_io.read_bytes,
            disk_io.write_bytes,
            current_rss,
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

    def success(self):
        if self.max_allowed_rss == 0:
            return super().success()
        res = self.max_rss <= self.max_allowed_rss
        if not res:
            msg = f"Max allowed RSS reached {humanize.naturalsize(self.max_rss)}"
        else:
            msg = "Excellent job, you did not kill the resources!"
        return res, msg

    def _stop(self, pid):
        if self.report_fd is None:
            self.warning("No data collected for psutil")
            return []

        self.report_fd.close()

        if self.max_allowed_rss == 0:
            threshold = None
        else:
            threshold = self.max_allowed_rss

        plot_files = self.generate_plots(
            self.report_file,
            [
                lambda row: float(row[5]),
                "Memory Usage (RSS)",
                "Bytes",
                "rss.png",
                tkr.FuncFormatter(humanize.naturalsize),
                threshold,
            ],
            [lambda row: float(row[11]), "CPU%", "%", "cpu.png", None, None],
            [lambda row: int(row[7]), "Threads", "ths", "threads.png", None, None],
            [lambda row: int(row[6]), "File Descriptors", "FDs", "fds.png", None, None],
            [lambda row: int(row[8]), "Context Switches", "ctx", "ctx.png", None, None],
            [
                lambda row: float(row[0]),
                "Disk Usage",
                "disk",
                "disk.png",
                tkr.FuncFormatter(humanize.naturalsize),
                None,
            ],
        )

        return [
            {"label": "Memory Usage", "file": plot_files[0], "type": "image"},
            {"label": "CPU Usage", "file": plot_files[1], "type": "image"},
            {"label": "Threads", "file": plot_files[2], "type": "image"},
            {"label": "FDs", "file": plot_files[3], "type": "image"},
            {"label": "Context Switch", "file": plot_files[4], "type": "image"},
            {"label": "Disk Usage", "file": plot_files[5], "type": "image"},
            {"label": "psutil CSV data", "file": self.report_file, "type": "artifact"},
        ]


register_plugin(ResourceWatcher)
