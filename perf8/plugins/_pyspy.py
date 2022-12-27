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
import sys
import subprocess
import shutil
from sys import platform
import base64
import time

from perf8.plugins.base import BasePlugin, register_plugin


PYSPY = "py-spy"
SPEEDSCOPE_APP = os.path.join(os.path.dirname(__file__), "..", "speedscope")


class PySpy(BasePlugin):
    name = "pyspy"
    fqn = f"{__module__}:{__qualname__}"
    in_process = False
    description = "Sampling profiler for Python"
    priority = 0
    supported = platform in ("linux", "linux2")

    def __init__(self, args):
        super().__init__(args)
        location = os.path.join(os.path.dirname(sys.executable), PYSPY)
        if os.path.exists(location):
            self.pyspy = location
        else:
            self.pyspy = shutil.which(PYSPY)
        if self.pyspy is None:
            raise Exception("Cannot find py-spy")

        # could be in the plugin metadata
        if not self.supported:
            self.info(f"pyspy support on {platform} is not great")
        self.profile_file = os.path.join(self.target_dir, "speedscope.json")
        self.proc = None

    def check_pid(self, pid):
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True

    def start(self, pid):
        running = self.check_pid(pid)
        start = time.time()
        while not running and time.time() - start < 120:
            self.warning(f"Process {pid} not running...")
            time.sleep(1.0)

        if not running:
            raise OSError(f"Process {pid} not running...")

        command = [
            self.pyspy,
            "record",
            "--nonblocking",
            "-s",
            "--format",
            "speedscope",
            "-o",
            self.profile_file,
            "--pid",
            str(pid),
        ]
        self.debug(f"Running {command}")

        self.proc = subprocess.Popen(command)
        while self.proc.pid is None:
            time.sleep(0.1)

        code = self.proc.poll()
        if code is not None:
            self.warning(f"pyspy exited immediately with code {code}")

    def stop(self, pid):
        self.debug("Pyspy should stop by itself...")
        running = self.check_pid(pid)
        start = time.time()
        while running and time.time() - start < 120:
            self.warning(f"Process {pid} still running. Waiting...")
            time.sleep(1.0)

        if self.proc.poll() is None:
            self.debug("Stopping Py-spy")
            self.proc.terminate()
            try:
                returncode = self.proc.wait(timeout=120)
                self.debug(f"return code is {returncode}")
            except subprocess.TimeoutExpired:
                self.proc.kill()

        # copy over the speedscope dir
        speedscope_copy = os.path.join(self.target_dir, "speedscope")
        if os.path.exists(speedscope_copy):
            shutil.rmtree(speedscope_copy)
        shutil.copytree(SPEEDSCOPE_APP, speedscope_copy)

        if not os.path.exists(self.profile_file):
            self.warning(f"Fail to find pyspy result at {self.profile_file}")
            return []

        # create the js script that contains the base64-ed results
        with open(self.profile_file, "rb") as f:
            data = f.read()
        data = base64.b64encode(data).strip().decode()

        # create the javascript file
        js_data = f"speedscope.loadFileFromBase64('speedscope.json', '{data}')"
        result_js = os.path.abspath(os.path.join(self.target_dir, "results.js"))

        with open(result_js, "w") as f:
            f.write(js_data)

        with open(os.path.join(self.target_dir, "pyspy.html"), "w") as f:
            f.write(
                f'<script>window.location="speedscope/index.html#localProfilePath={result_js}"</script>'
            )

        return [
            {
                "label": "Performance speedscope",
                "file": self.profile_file,
                "type": "artifact",
            },
            {
                "label": "Py-spy Performance",
                "file": os.path.join(self.target_dir, "pyspy.html"),
                "type": "html",
            },
        ]


register_plugin(PySpy)
