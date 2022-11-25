perf8
=====

.. image:: https://github.com/tarekziade/perf8/actions/workflows/ci.yml/badge.svg?branch=main
   :target: https://github.com/tarekziade/perf8/actions/workflows/ci.yml?query=branch%3Amain


**THIS IS ALPHA QUALITY, UNSUPPORTED, RUN AT YOUR OWN RISKS**

Your Tool For Python Performance Tracking

`perf8` is a curated list of tools to track the performance of your Python app.

The project is pluggable, and ships with a few tools:

- perf8-gprof2dot - a cProfile to dot graph generator
- perf8-spypy - a spy-py flamegraph generator
- perf8-memray - a memory flamegraph generator
- perf8-psutil - a psutil integration

Running the `perf8` command against your Python module:

.. code-block:: sh

   perf8 --memray --psutil --spypy /my/python/script.py

Will generate a self-contained HTML report, making it suitable for
running it in automation and produce performance artifacts.

.. image:: docs/perf8-screencast.gif
