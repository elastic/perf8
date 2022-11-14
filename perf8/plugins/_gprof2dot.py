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

        return [self.outfile, "profile.dot", "profile.png"]


register_plugin(Profiler)
