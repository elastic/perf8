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
from importlib_metadata import distribution
from memray import Tracker, FileDestination  # , FileReader
import os
import sys
from copy import copy

from perf8.plugins.base import BasePlugin, register_plugin


def load_entry_point(spec, group, name):
    dist_name, _, _ = spec.partition("==")
    matches = (
        entry_point
        for entry_point in distribution(dist_name).entry_points
        if entry_point.group == group and entry_point.name == name
    )
    return next(matches).load()


class MemoryProfiler(BasePlugin):
    name = "memray"
    in_process = True
    description = "Runs memray and generates a flamegraph"

    def __init__(self, args):
        super().__init__(args)
        self.outfile = os.path.join(args.target_dir, "memreport")
        self.destination = FileDestination(
            path=self.outfile, overwrite=True, compress_on_exit=True
        )
        if os.path.exists(self.outfile):
            os.remove(self.outfile)

        self.report_path = os.path.join(
            args.target_dir, "memray-flamegraph-report.html"
        )
        if os.path.exists(self.report_path):
            os.remove(self.report_path)
        self.tracker = Tracker(
            destination=self.destination,
            # native_traces=True,
            follow_fork=True,
            trace_python_allocators=True,
        )

    def _enable(self):
        self.tracker.__enter__()

    def _disable(self):
        self.tracker.__exit__(None, None, None)

    def report(self):
        old_args = copy(sys.argv)
        sys.argv[:] = ["memray", "flamegraph", self.outfile, "-o", self.report_path]
        try:
            load_entry_point("memray", "console_scripts", "memray")()
        except SystemExit:
            pass

        sys.argv[:] = old_args
        return [
            {"label": "Memory Flamegraph", "file": self.report_path, "type": "html"},
            {"label": "memray dump", "file": self.outfile, "type": "artifact"},
        ]


register_plugin(MemoryProfiler)
