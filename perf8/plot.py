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
import matplotlib.ticker as tkr

plt.figure(figsize=(14, 10))


class Line:
    def __init__(self, extractor, title, threshold, color):
        self.extractor = extractor
        self.title = title
        self.threshold = threshold
        self.color = color


class Graph:
    def __init__(self, title, target_dir, target_file, ylabel, yformatter, *lines):
        self.lines = lines
        self.target_file = target_file
        self.target_dir = target_dir
        self.plot_file = os.path.join(target_dir, target_file)
        self.ylabel = ylabel
        self.title = title
        self.yformatter = yformatter

    def annotate_max(self, x_max, y_max, ax, yaxis):
        if self.yformatter:
            formatter = self.yformatter
        else:
            formatter = tkr.StrMethodFormatter("{x:,g}")
        formatter.set_axis(yaxis)
        text = formatter(y_max)
        ax.annotate(
            text,
            xy=(x_max, y_max),
            xycoords="data",
            xytext=(0, 0),
            textcoords="offset points",
            ha="center",
            va="center",
            arrowprops=dict(arrowstyle="->", color="black"),
            bbox=dict(boxstyle="square,pad=0.3", fc="w", ec="red"),
        )

    def generate(self, plugin, path_or_rows):
        if isinstance(path_or_rows, str):
            with open(path_or_rows) as cvsfile:
                samples = [line for line in csv.reader(cvsfile, delimiter=",")]
        else:
            samples = path_or_rows

        plt.clf()

        ax = plt.gca()

        for line in self.lines:
            x = []
            y = []
            y_max = x_max = 0
            for i, row in enumerate(samples):
                if i == 0:
                    continue
                value = line.extractor(row)
                if value > y_max:
                    y_max = value
                    x_max = row[-1]
                x.append(row[-1])
                y.append(value)

            plt.plot(
                x, y, color=line.color, linestyle="dashed", marker="o", label=line.title
            )
            if x:
                xtick_step = int(len(x) / 10) if len(x) > 9 else 1
                existing_ticks = ax.get_xticks()
                ticks = list(existing_ticks[::xtick_step])
                # If last tick is missing, add it!
                if ticks[-1] != x[-1]:
                    ticks.append(existing_ticks[-1])
                ax.set_xticks(ticks)

            if line.threshold is not None and line.threshold < y_max:
                plt.axhline(line.threshold, color="r")

            plt.plot(x_max, y_max, "ro")
            self.annotate_max(x_max, y_max, ax, ax.yaxis)

        plt.legend(loc=3)
        plt.xticks(rotation=25)
        plt.xlabel("Duration (s)")
        plt.ylabel(self.ylabel)
        ax = plt.gca()

        if self.yformatter:
            ax.yaxis.set_major_formatter(self.yformatter)
        else:
            ax.yaxis.set_major_formatter(tkr.StrMethodFormatter("{x:,g}"))

        plt.title(self.title, fontsize=20)
        plt.grid()
        plugin.info(f"Saved plot file at {self.plot_file}")
        plt.savefig(self.plot_file)
        return self.plot_file
