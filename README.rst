perf8
=====

.. image:: https://github.com/tarekziade/perf8/actions/workflows/ci.yml/badge.svg?branch=main
   :target: https://github.com/tarekziade/perf8/actions/workflows/ci.yml?query=branch%3Amain


**THIS IS ALPHA QUALITY, UNSUPPORTED, RUN AT YOUR OWN RISKS**

Your Tool For Python Performance Tracking

`perf8` is a curated list of tools to track the performance of your Python app.

The project is pluggable, and ships with a few tools:

- cprofile - a cProfile to Dot graph generator
- pyspy - a py-spy speedscope generator
- memray - a memory flamegraph generator
- psutil - a psutil integration
- asyncstats - stats on the asyncio eventloop usage (for async apps)

Installation
------------

Use `pip`:

.. code-block:: sh

   pip install perf8

If you use the `cprofile` plugin, you will need to install `Graphviz` to
get the `dot` utility. See. https://graphviz.org/download/



Usage
-----

Running the `perf8` command against your Python module:

.. code-block:: sh

   perf8 --all -c /my/python/script.py --option1

Will generate a self-contained HTML report, making it suitable for
running it in automation and produce performance artifacts.

You can pick specific plugins. Run `perf --help` and use the ones you want.


Async applications
------------------

Running the `asyncstats` plugin requires to provide your application event loop.

In order to do this, you need to instrument your application to give `perf8`
the loop to watch. You can use the `enable` and `disable` coroutines:

.. code-block:: python

   import perf8

   async def my_app():
        await perf8.enable(my_loop)
        try:
            # my code
            await run_app()
        finally:
            await perf8.disable()


To avoid running this code in production you can use the `PERF8` environment variable
to detect if `perf8` is calling your app:


.. code-block:: python

   import os

   if 'PERF8' in os.environ:
       import perf8

       async with perf8.measure():
           await run_app()
    else:
        await run_app()


Screencast
----------

.. image:: docs/perf8-screencast.gif
