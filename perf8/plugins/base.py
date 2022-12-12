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
import csv
import os

import matplotlib.pyplot as plt


_PLUGINS = []


def register_plugin(klass):
    if klass.supported:
        _PLUGINS.append(klass)


def get_registered_plugins():
    # this import will load all internal plugins modules
    # so they have a chance to register them selves
    from perf8 import plugins  # NOQA

    return _PLUGINS


class BasePlugin:
    name = ""
    in_process = False
    description = ""
    is_async = False
    priority = 0
    supported = True

    def __init__(self, args):
        self.args = args
        self.target_dir = args.target_dir

    @classmethod
    @property
    def fqn(cls):
        return f"{cls.__module__}:{cls.__qualname__}"

    def enable(self):
        raise NotImplementedError

    def disable(self):
        raise NotImplementedError

    def report(self):
        raise NotImplementedError

    async def probe(self, pid):
        pass

    def generate_plot(self, path, extract_field, title, ylabel, target):
        x = []
        y = []

        with open(path) as csvfile:
            lines = csv.reader(csvfile, delimiter=",")
            for i, row in enumerate(lines):
                if i == 0:
                    continue
                x.append(row[-1])
                y.append(extract_field(row))

        plt.cla()
        plt.plot(x, y, color="g", linestyle="dashed", marker="o", label=title)

        plt.xticks(rotation=25)
        plt.xlabel("Duration")
        plt.ylabel(ylabel)
        plt.title(title, fontsize=20)
        plt.grid()
        plt.legend()
        plot_file = os.path.join(self.target_dir, target)
        plt.savefig(plot_file)
        return plot_file


class AsyncBasePlugin(BasePlugin):
    is_async = True

    async def enable(self, loop):
        raise NotImplementedError

    async def disable(self):
        raise NotImplementedError
