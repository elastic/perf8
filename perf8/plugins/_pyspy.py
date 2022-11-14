import os
import subprocess
import shutil
import signal
from sys import platform

from perf8.util import register_plugin


class PySpy:
    name = "pyspy"
    fqn = f"{__module__}:{__qualname__}"
    in_process = False
    description = "Sampling profiler for Python"

    def __init__(self, args):
        self.target_dir = args.target_dir
        self.pyspy = shutil.which("py-spy")
        if self.pyspy is None:
            raise Exception("Cannot find py-spy")

        # could be in the plugin metadata
        if platform not in ("linux", "linux2"):
            raise Exception(f"pyspy not supported on {platform}")
        self.profile_file = os.path.join(self.target_dir, "pyspy.svg")
        self.proc = None

    def start(self, pid):
        command = [self.pyspy, "record", "-o", self.profile_file, "--pid", str(pid)]
        self.proc = subprocess.Popen(command)

    async def probe(self, pid):
        pass

    def stop(self, pid):
        os.kill(self.proc.pid, signal.SIGTERM)

        return [self.profile_file]


register_plugin(PySpy)
