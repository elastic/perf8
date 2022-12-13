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
import shutil
import pstats
from subprocess import check_call
import sys
import os

try:
    from cProfile import Profile
except ImportError:
    from Profile import Profile

from perf8.plugins.base import BasePlugin, register_plugin


GPROF2DOT = "gprof2dot"


class Profiler(BasePlugin):
    name = "cprofile"
    in_process = True
    description = "Runs cProfile and generate a dot graph with gprof2dot"
    priority = 0
    supported = True

    def __init__(self, args):
        super().__init__(args)
        self.outfile = os.path.join(self.target_dir, "profile.data")
        self.dotfile = os.path.join(self.target_dir, "profile.dot")
        self.pngfile = os.path.join(self.target_dir, "profile.png")
        self.profiler = Profile()
        location = os.path.join(os.path.dirname(sys.executable), GPROF2DOT)
        if os.path.exists(location):
            self.gprof2dot = location
        else:
            self.gprof2dot = shutil.which(GPROF2DOT)

    def get_profiler(self, *args, **kw):
        return self.profiler

    def _enable(self):
        self.profiler.enable()

    def _disable(self):
        self.profiler.disable()

    def report(self):
        # create a pstats file
        self.profiler.create_stats()
        self.profiler.dump_stats(self.outfile)
        stats = pstats.Stats(self.outfile)
        stats = stats.strip_dirs()
        stats.dump_stats(self.outfile)

        # create a dot file from the pstats file
        check_call(
            [
                sys.executable,
                self.gprof2dot,
                "-f",
                "pstats",
                self.outfile,
                "-o",
                self.dotfile,
            ]
        )

        # render the dot file into a png
        check_call(["dot", "-o", self.pngfile, "-Tpng", self.dotfile])

        return [
            {"label": "cProfile dot file", "file": self.dotfile, "type": "artifact"},
            {"label": "cProfile png output", "file": self.pngfile, "type": "image"},
            {"label": "cProfile pstats file", "file": self.outfile, "type": "artifact"},
        ]


register_plugin(Profiler)
