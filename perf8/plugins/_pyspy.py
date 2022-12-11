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
import signal
from sys import platform
import base64

from perf8.util import register_plugin


PYSPY = "py-spy"
SPEEDSCOPE_APP = os.path.join(os.path.dirname(__file__), "..", "speedscope")


class PySpy:
    name = "pyspy"
    fqn = f"{__module__}:{__qualname__}"
    in_process = False
    description = "Sampling profiler for Python"

    def __init__(self, args):
        self.target_dir = args.target_dir
        location = os.path.join(os.path.dirname(sys.executable), PYSPY)
        if os.path.exists(location):
            self.pyspy = location
        else:
            self.pyspy = shutil.which(PYSPY)
        if self.pyspy is None:
            raise Exception("Cannot find py-spy")

        # could be in the plugin metadata
        if platform not in ("linux", "linux2"):
            print(f"pyspy support on {platform} is not great")
        self.profile_file = os.path.join(self.target_dir, "speedscope.json")
        self.proc = None

    def start(self, pid):
        command = [
            self.pyspy,
            "record",
            "-s",
            "--format",
            "speedscope",
            "-o",
            self.profile_file,
            "--pid",
            str(pid),
        ]
        self.proc = subprocess.Popen(command)

    async def probe(self, pid):
        pass

    def stop(self, pid):
        os.kill(self.proc.pid, signal.SIGTERM)

        # copy over the speedscope dir
        speedscope_copy = os.path.join(self.target_dir, "speedscope")
        if os.path.exists(speedscope_copy):
            shutil.rmtree(speedscope_copy)
        shutil.copytree(SPEEDSCOPE_APP, speedscope_copy)

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
