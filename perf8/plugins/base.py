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
import importlib
import asyncio
import csv
import os
import contextlib

import matplotlib.pyplot as plt
from perf8.logger import logger


_ASYNC_PLUGINS_INSTANCES = []
_PLUGINS_INSTANCES = {}


def get_plugin_klass(fqn):
    module_name, klass_name = fqn.split(":")
    module = importlib.import_module(module_name)
    return getattr(module, klass_name)


def set_plugins(plugins):
    for plugin in plugins:
        _PLUGINS_INSTANCES[plugin.name] = plugin


async def enable(loop=None):
    if "PERF8" not in os.environ:
        return

    if loop is None:
        loop = asyncio.get_event_loop()

    for name in os.environ.get("PERF8_ASYNC_PLUGIN", "").split(","):
        name = name.strip()
        if name == "":
            continue
        plugin = _PLUGINS_INSTANCES[name]
        await plugin.enable(loop)
        _ASYNC_PLUGINS_INSTANCES.append(plugin)

    if len(_ASYNC_PLUGINS_INSTANCES) == 0:
        logger.warning("No perf8 async plugin was activated")


async def disable():
    for plugin in _ASYNC_PLUGINS_INSTANCES:
        await plugin.disable()
    _ASYNC_PLUGINS_INSTANCES[:] = []


@contextlib.asynccontextmanager
async def measure(loop=None):
    await enable(loop)
    try:
        yield
    finally:
        await disable()


_PLUGIN_CLASSES = []


def register_plugin(klass):
    if klass.supported:
        _PLUGIN_CLASSES.append(klass)


def get_registered_plugins():
    # this import will load all internal plugins modules
    # so they have a chance to register them selves
    from perf8 import plugins  # NOQA

    return _PLUGIN_CLASSES


class BasePlugin:
    name = ""
    in_process = False
    description = ""
    is_async = False
    priority = 0
    supported = True
    arguments = []

    def __init__(self, args):
        self.args = args
        self.target_dir = args.target_dir
        self.enabled = False

    def check_pid(self, pid):
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True

    def success(self):
        return True, "Looking good"

    def start(self, pid):
        self.enabled = True
        self._start(pid)

    def stop(self, pid=None):
        self.enabled = False
        if pid is not None:
            res = self._stop(pid)
        else:
            res = []
        return res + [{"result": self.success(), "type": "result", "name": self.name}]

    @classmethod
    @property
    def fqn(cls):
        return f"{cls.__module__}:{cls.__qualname__}"

    def debug(self, msg):
        logger.debug(f"[{os.getpid()}][{self.name}] {msg}")

    def info(self, msg):
        logger.info(f"[{os.getpid()}][{self.name}] {msg}")

    def warning(self, msg):
        logger.warning(f"[{os.getpid()}][{self.name}] {msg}")

    def disable(self):
        if not self.enabled:
            return
        self._disable()
        self.enabled = False

    def enable(self):
        if self.enabled:
            return
        self._enable()
        self.enabled = True

    def _enable(self):
        raise NotImplementedError

    def _disable(self):
        raise NotImplementedError

    def report(self):
        raise NotImplementedError

    async def probe(self, pid):
        pass

    def generate_plots(self, path, *plot_defs):
        # load lines once
        rows = []
        with open(path) as csvfile:
            lines = csv.reader(csvfile, delimiter=",")
            for row in lines:
                rows.append(row)

        self.info(f"Loaded {len(rows)} data points from {path}")
        plots = []
        for extract_field, title, ylabel, target, yformatter, threshold in plot_defs:
            plots.append(
                self.generate_plot(
                    rows, extract_field, title, ylabel, target, yformatter, threshold
                )
            )
        return plots

    def generate_plot(
        self,
        path_or_rows,
        extract_field,
        title,
        ylabel,
        target,
        yformatter,
        threshold=None,
    ):
        x = []
        y = []

        if isinstance(path_or_rows, str):
            cvsfile = open(path_or_rows)
            lines = csv.reader(cvsfile, delimiter=",")
        else:
            lines = path_or_rows
            cvsfile = None

        max = 0
        try:
            for i, row in enumerate(lines):
                if i == 0:
                    continue
                value = extract_field(row)
                if value > max:
                    max = value
                x.append(row[-1])
                y.append(value)
        finally:
            if cvsfile is not None:
                cvsfile.close()

        plt.clf()
        ax = plt.gca()

        plt.plot(x, y, color="g", linestyle="dashed", marker="o", label=title)

        plt.xticks(rotation=25)
        plt.xlabel("Duration (s)")

        if x:
            xtick_step = int(len(x) / 10) if len(x) > 9 else 1
            existing_ticks = ax.get_xticks()
            ticks = list(existing_ticks[::xtick_step])
            # If last tick is missing, add it!
            if ticks[-1] != x[-1]:
                ticks.append(existing_ticks[-1])
            ax.set_xticks(ticks)

        plt.ylabel(ylabel)
        if yformatter:
            ax.yaxis.set_major_formatter(yformatter)
        plt.title(title, fontsize=20)
        if threshold is not None and threshold < max:
            plt.axhline(threshold, color="r")
        plt.grid()
        self._annotate_max(plt, ax, x, y, yformatter)
        plot_file = os.path.join(self.target_dir, target)
        self.info(f"Saved plot file at {plot_file}")
        plt.savefig(plot_file)
        return plot_file

    def _annotate_max(self, plt, ax, x, y, yformatter=None):
        """
        This function creates a second plot on top of original one
        and marks only the maximum value on it.

        Also adds another yaxis on the right wthat has only
        label for the maximum value
        """
        if not x or not y:
            return

        # Get the coordinate for maximum Y
        ymax = max(y)
        x_for_ymax = x[y.index(ymax)]

        # Copy the plot while also moving
        # Yaxis labels to the right
        ax2 = ax.twinx()

        # First draw same figure but invisible
        # Why? Cause otherwise Y axis label will
        # look weird :(
        ax2.plot(x, y, "r-", alpha=0)

        # Also draw red dot for the max value
        ax2.plot(x_for_ymax, ymax, "ro")

        # Keep only label for maximum Y on our axis
        ax2.set_yticks([ymax])

        # Don't forget to format it
        if yformatter:
            ax2.yaxis.set_major_formatter(yformatter)


class AsyncBasePlugin(BasePlugin):
    is_async = True

    async def disable(self):
        if not self.enabled:
            return
        await self._disable()

    async def enable(self, loop):
        if self.enabled:
            return
        await self._enable(loop)

    async def _enable(self, loop):
        raise NotImplementedError

    async def _disable(self):
        raise NotImplementedError
