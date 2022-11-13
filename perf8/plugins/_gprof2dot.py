import os
import sys
from copy import copy
import gprof2dot
import pstats
from subprocess import check_call

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

    def run(self, command):
        progname = command[0]
        extra_args = command[1:]

        code = compile(
            open(progname, mode="rb").read(), "__main__", "exec", dont_inherit=True
        )
        fname = progname

        globs = {}
        globs["__file__"] = fname
        globs["__name__"] = "__main__"
        globs["__package__"] = None

        s = Profile()
        saved = copy(sys.argv[:])
        sys.argv[:] = [fname] + extra_args
        sys.path.insert(0, os.path.dirname(progname))
        try:
            s.runctx(code, globs, None)
        except SystemExit:
            pass
        sys.argv[:] = saved
        # create a pstats file
        s.create_stats()

        s.dump_stats(self.outfile)
        stats = pstats.Stats(self.outfile)
        stats = stats.strip_dirs()
        stats.dump_stats(self.outfile)

        # create a dot file from the pstats file
        gprof2dot.main(["-f", "pstats", self.outfile, "-o", "profile.dot"])

        # render the dot file into a png
        check_call(["dot", "-o", "profile.png", "-Tpng", "profile.dot"])

    def stop(self, pid):
        pass


register_plugin(Profiler)
