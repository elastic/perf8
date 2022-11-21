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
import gprof2dot
import pstats
from subprocess import check_call
import sys

try:
    from cProfile import Profile
except ImportError:
    from Profile import Profile

from perf8.util import register_plugin


class Profiler:
    name = "gprof2dot"
    fqn = f"{__module__}:{__qualname__}"
    in_process = True
    description = "Runs cProfile and generate a dot graph with gprof2dot"

    def __init__(self, args):
        self.outfile = "profile.data"
        self.flameout = "profile.svg"
        self.profiler = Profile()

    def get_profiler(self, *args, **kw):
        return self.profiler

    def enable(self):
        self.profiler.enable()
        sys.setprofile(self.get_profiler)

    def disable(self):
        self.profiler.disable()

    def report(self):
        # create a pstats file
        self.profiler.create_stats()
        self.profiler.dump_stats(self.outfile)
        stats = pstats.Stats(self.outfile)
        stats = stats.strip_dirs()
        stats.dump_stats(self.outfile)

        # create a dot file from the pstats file
        gprof2dot.main(["-f", "pstats", self.outfile, "-o", "profile.dot"])

        # render the dot file into a png
        check_call(["dot", "-o", "profile.png", "-Tpng", "profile.dot"])

        return [
            {"label": "gprof2dot dot file", "file": "profile.dot"},
            {"label": "gprof2dot png output", "file": "profile.png"},
        ]


register_plugin(Profiler)
