import importlib
import sys
from copy import copy
import os


def get_plugin_klass(fqn):
    module_name, klass_name = fqn.split(":")
    module = importlib.import_module(module_name)
    return getattr(module, klass_name)


_PLUGINS = []


def register_plugin(klass):
    _PLUGINS.append(klass)


def get_registered_plugins():
    # this import will load all internal plugins modules
    # so they have a chance to register them selves
    from perf8 import plugins  # NOQA

    return _PLUGINS


def get_code(script):
    with open(script, mode="rb") as f:
        return compile(f.read(), "__main__", "exec", dont_inherit=True)


def run_script(script_file, script_args):
    globs = {}
    globs["__file__"] = script_file
    globs["__name__"] = "__main__"
    globs["__package__"] = None
    saved = copy(sys.argv[:])
    sys.argv[:] = [script_file] + script_args
    sys.path.insert(0, os.path.dirname(script_file))
    try:
        exec(get_code(script_file), globs, None)
    except SystemExit:
        pass
    sys.argv[:] = saved
