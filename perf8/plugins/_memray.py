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
from memray import Tracker, FileDestination  # , FileReader

# from memray.reporters.flamegraph import FlameGraphReporter

from perf8.util import register_plugin


class MemoryProfiler:
    name = "memray"
    fqn = f"{__module__}:{__qualname__}"
    in_process = True
    description = "Runs memray and generates a flamegraph"

    def __init__(self, args):
        self.outfile = "memory.bin"
        self.destination = FileDestination(
            path=self.outfile, overwrite=True, compress_on_exit=True
        )

        # native = True
        self.tracker = Tracker(destination=self.destination, native_traces=False)

    def enable(self):
        self.tracker.__enter__()

    def disable(self):
        self.tracker.__exit__(None, None, None)

    def report(self):
        return []

        # reader = FileReader(self.outfile)
        # reporter = FlameGraphReporter.from_snapshot(
        #    reader.get_allocation_records(),
        #    memory_records=reader.get_memory_snapshots(),
        #    native_traces=False,
        # )
        # return ["flamegraph.png"]


register_plugin(MemoryProfiler)
