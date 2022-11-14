import sys
import subprocess
import asyncio
import time
import importlib
import argparse
import shlex
import signal
import os

from perf8 import __version__
from perf8.util import get_registered_plugins


def _parser():
    parser = argparse.ArgumentParser(
        description="Python Performance Tracking.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    for plugin in get_registered_plugins():
        parser.add_argument(
            f"--{plugin.name}",
            action="store_true",
            default=False,
            help=plugin.description,
        )
        # XXX ask the plugin for its arguments and set them in a group

    parser.add_argument(
        "--refresh-rate",
        type=int,
        default=5,
        help="Refresh rate",
    )

    parser.add_argument(
        "-c",
        "--command",
        default="dummy.py --with-option -a=2",
        type=str,
        nargs=argparse.REMAINDER,
        help="Command to run",
    )

    parser.add_argument(
        "--version",
        action="store_true",
        default=False,
        help="Displays version and exits.",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help=(
            "Verbosity level. -v will display "
            "tracebacks. -vv requests and responses."
        ),
    )

    return parser


def main(args=None):
    if args is None:
        parser = _parser()
        args = parser.parse_args()

    if args.version:
        print(__version__)
        sys.exit(0)

    p = WatchedProcess(args)
    asyncio.run(p.run())
    return 0


class WatchedProcess:
    def __init__(self, args):
        self.args = args
        self.cmd = args.command
        self.proc = self.pid = None
        self.every = args.refresh_rate
        self.plugins = [
            plugin for plugin in get_registered_plugins() if getattr(args, plugin.name)
        ]
        self.out_plugins = [
            plugin(self.args) for plugin in self.plugins if not plugin.in_process
        ]
        self.reports = {}
        signal.signal(signal.SIGINT, self.exit)
        signal.signal(signal.SIGTERM, self.exit)

    def exit(self, signum, frame):
        print(f"We got a {signum} signal, passing it along")
        os.kill(self.proc.pid, signum)

    async def _probe(self):
        while self.proc.poll() is None:
            for plugin in self.out_plugins:
                await plugin.probe(self.pid)
            if self.proc.poll() is not None:
                break
            await asyncio.sleep(self.every)

    def start(self):
        print(f"[perf8] Plugins: {', '.join([p.name for p in self.plugins])}")
        for plugin in self.out_plugins:
            plugin.start(self.pid)

    def stop(self):
        for plugin in self.out_plugins:
            self.reports[plugin.name] = plugin.stop(self.pid)

    async def run(self):
        start = time.time()
        plugins = [plugin.fqn for plugin in self.plugins if plugin.in_process]

        # XXX pass-through perf8 args so the plugins can pick there options
        cmd = [
            sys.executable,
            "-m",
            "perf8.runner",
            "--plugins",
            ",".join(plugins),
            "-s",
        ] + self.cmd

        print(f"[perf8] Running {shlex.join(cmd)}")
        try:
            self.proc = subprocess.Popen(cmd)
            while self.proc.pid is None:
                await asyncio.sleep(1.0)
            self.pid = self.proc.pid
            self.start()

            await self._probe()
        finally:
            self.stop()

        self.proc.wait()
        print(f"[perf8] Total seconds {time.time()-start}")
        print("[perf8] Reports generated:")
        for plugin in self.plugins:
            if plugin.name not in self.reports:
                continue
            print(
                f"[perf8] Plugin {plugin.name} generated {','.join(self.reports[plugin.name])}"
            )
        with open("report.txt") as f:
            for line in f.readlines():
                line = line.strip().split(":")
                if len(line) != 2:
                    continue
                plugin, reports = line
                print(f"[perf8] Plugin {plugin} generated {reports}")

    def _plugin_klass(self, fqn):
        module_name, klass_name = fqn.split(":")
        module = importlib.import_module(module_name)
        return getattr(module, klass_name)


if __name__ == "__main__":
    main()
