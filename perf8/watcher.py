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
import sys
import subprocess
import asyncio
import time
import importlib
import shlex
import signal
import os
from collections import defaultdict

import humanize

from perf8.plugins.base import get_registered_plugins
from perf8.reporter import Reporter
from perf8.logger import logger


HERE = os.path.dirname(__file__)


class WatchedProcess:
    def __init__(self, args):
        self.args = args
        self.cmd = args.command
        if not isinstance(self.cmd, str):
            self.cmd = shlex.join(self.cmd)
        self.proc = self.pid = None
        self.every = args.refresh_rate
        self.plugins = [
            plugin for plugin in get_registered_plugins() if getattr(args, plugin.name)
        ]
        self.out_plugins = [
            plugin(self.args) for plugin in self.plugins if not plugin.in_process
        ]
        self.out_reports = defaultdict(list)
        os.makedirs(self.args.target_dir, exist_ok=True)
        signal.signal(signal.SIGINT, self.exit)
        signal.signal(signal.SIGTERM, self.exit)
        signal.signal(signal.SIGUSR1, self.runner_exit)
        self.started = False

    def exit(self, signum, frame):
        logger.info(f"We got a {signum} signal, passing it along")
        os.kill(self.proc.pid, signum)

    def runner_exit(self, signum, frame):
        logger.info(f"We got a {signum} signal, the app finished execution")
        logger.info("The app wrapper is now building in-process reports")
        # we can stop out of process plugins
        self.stop()

    async def _probe(self):
        logger.info(f"Starting the probing -- every {self.every} seconds")

        while self.started:
            for plugin in self.out_plugins:
                if not plugin.enabled:
                    continue
                await plugin.probe(self.pid)
                logger.debug(f"Sent a probe to {plugin.name}")
            if self.proc.poll() is not None:
                break
            await asyncio.sleep(self.every)

    def start(self):
        logger.info(f"[perf8] Plugins: {', '.join([p.name for p in self.plugins])}")
        self.started = True
        for plugin in self.out_plugins:
            plugin.start(self.pid)

    def stop(self):
        if not self.started:
            return
        try:
            for plugin in self.out_plugins:
                self.out_reports[plugin.name].extend(plugin.stop(self.pid))
        finally:
            self.started = False

    async def run(self):
        plugins = [plugin.fqn for plugin in self.plugins if plugin.in_process]

        # XXX pass-through perf8 args so the plugins can pick there options
        cmd = [
            sys.executable,
            "-m",
            "perf8.runner",
            "-t",
            self.args.target_dir,
            "--ppid",
            str(os.getpid()),
        ]

        if len(plugins) > 0:
            cmd.extend(["--plugins", ",".join(plugins)])

        cmd.extend(["-s", self.cmd])
        cmd = [str(item) for item in cmd]

        logger.info(f"[perf8] Running {shlex.join(cmd)}")
        start = time.time()
        try:
            self.proc = subprocess.Popen(cmd)
            while self.proc.pid is None:
                await asyncio.sleep(1.0)
            self.pid = self.proc.pid
            self.start()

            await self._probe()
            execution_time = time.time() - start
            logger.info(f"Command execution time {execution_time:.2f} seconds.")
        finally:
            self.stop()

        self.proc.wait()

        execution_info = {"duration": humanize.precisedelta(execution_time)}
        report_json = os.path.join(self.args.target_dir, "report.json")
        reporter = Reporter(self.args, execution_info)
        html_report = reporter.generate(report_json, self.out_reports, self.plugins)
        logger.info(f"Find the full report at {html_report}")

    def _plugin_klass(self, fqn):
        module_name, klass_name = fqn.split(":")
        module = importlib.import_module(module_name)
        return getattr(module, klass_name)
