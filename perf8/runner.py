"""
Wrapper script
"""
import argparse
from perf8.util import get_plugin_klass


def main():

    parser = argparse.ArgumentParser(
        description="Perf8 Wrapper",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--plugins",
        type=str,
        default="",
        help="Plugins to use",
    )
    parser.add_argument(
        "-s",
        "--script",
        default="dummy.py --with-option -a=2",
        type=str,
        nargs=argparse.REMAINDER,
        help="Python script to run",
    )

    # XXX pass-through perf8 args so the plugins can pick there options
    args = parser.parse_args()

    plugins = [get_plugin_klass(fqn)(args) for fqn in args.plugins.split(",")]

    # running sequentially for now -- need to find a way to combine runs
    for plugin in plugins:
        plugin.run(command=args.script)


if __name__ == "__main__":
    main()
