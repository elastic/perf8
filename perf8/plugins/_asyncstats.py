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
import matplotlib.pyplot as plt
import csv
import time
import asyncio

from perf8.util import register_plugin


class EventLoopMonitoring:
    name = "asyncstats"
    fqn = f"{__module__}:{__qualname__}"
    in_process = True
    description = "Stats on the event loop"
    is_async = True
    priority = 0
    supported = True

    def __init__(self, args):
        self.target_dir = args.target_dir
        self.loop = self._prober = self.started_at = None
        self._idle_time = 1
        self._running = False
        self.report_fd = self.writer = self.proc_info = None
        self.report_file = os.path.join(args.target_dir, "loop.csv")

    async def _probe(self):
        while self._running:
            loop_time = self.loop.time()
            await asyncio.sleep(self._idle_time)
            lag = self.loop.time() - loop_time - self._idle_time
            when = time.time()
            metrics = (
                lag,
                len(asyncio.all_tasks(self.loop)),
                when,
                int(when - self.started_at),
            )
            self.writer.writerow(metrics)

    async def enable(self, loop):
        self.loop = loop
        self.report_fd = open(self.report_file, "w")
        self.writer = csv.writer(self.report_fd)
        self.started_at = time.time()
        self.rows = (
            "lag",
            "num_tasks",
            "when",
            "since",
        )
        # headers
        self.writer.writerow(self.rows)
        self._running = True
        self._prober = asyncio.create_task(self._probe())

    async def disable(self):
        self._running = False
        if self._prober is not None:
            await asyncio.sleep(0)
            await self._prober

    def generate_plot(self, path, extract_field, title, ylabel, target):
        x = []
        y = []

        with open(path) as csvfile:
            lines = csv.reader(csvfile, delimiter=",")
            for i, row in enumerate(lines):
                if i == 0:
                    continue
                x.append(row[-1])
                y.append(extract_field(row))

        plt.cla()
        plt.plot(x, y, color="g", linestyle="dashed", marker="o", label=title)

        plt.xticks(rotation=25)
        plt.xlabel("Duration")
        plt.ylabel(ylabel)
        plt.title(title, fontsize=20)
        plt.grid()
        plt.legend()
        plot_file = os.path.join(self.target_dir, target)
        plt.savefig(plot_file)
        return plot_file

    def report(self):
        if self.report_fd is None:
            return []

        self.report_fd.close()

        def extract_lag(row):
            return float(row[0])

        def extract_tasks(row):
            return int(row[1])

        loop_file = self.generate_plot(
            self.report_file, extract_lag, "Event loop lag", "Seconds", "loop_lag.png"
        )
        coro_file = self.generate_plot(
            self.report_file,
            extract_tasks,
            "Tasks concurrency",
            "tasks",
            "loop_coro.png",
        )

        return [
            {"label": "Event loop lag", "file": loop_file, "type": "image"},
            {"label": "Task concurrency", "file": coro_file, "type": "image"},
            {
                "label": "Event loop CSV data",
                "file": self.report_file,
                "type": "artifact",
            },
        ]


register_plugin(EventLoopMonitoring)
