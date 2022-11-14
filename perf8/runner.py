"""
Wrapper script
"""
import argparse
from perf8.util import get_plugin_klass, run_script


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
        "-r",
        "--report",
        default="report.txt",
        type=str,
        help="report file",
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

    script = args.script[0]
    script_args = args.script[1:]

    with open(args.report, "w") as f:
        # does exec() respects signals?
        if len(plugins) > 0:
            # running sequentially for now -- need to find a way to combine runs
            for plugin in plugins:
                reports = plugin.run(script, script_args)
                f.write(f"{plugin.name}:{','.join(reports)}\n")
        else:
            # no in-process plugins, we just run it
            run_script(script, script_args)


if __name__ == "__main__":
    main()
