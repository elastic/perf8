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
        self.pyspy = shutil.which("py-spy")
        if self.pyspy is None:
            raise Exception("Cannot find py-spy")

        # could be in the plugin metadata
        if platform not in ("linux", "linux2"):
            raise Exception(f"pyspy not supported on {platform}")
        self.profile_file = "profile.pyspy"
        self.proc = None

    def start(self, pid):
        command = [self.pyspy, "record", "--pid", str(pid)]
        self.proc = subprocess.Popen(command)

    async def probe(self, pid):
        pass

    def stop(self, pid):
        os.kill(self.proc.pid, signal.SIGTERM)

        return []


register_plugin(PySpy)
