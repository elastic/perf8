perf8
=====

.. image:: https://github.com/tarekziade/perf8/actions/workflows/ci.yml/badge.svg?branch=main
   :target: https://github.com/tarekziade/perf8/actions/workflows/ci.yml?query=branch%3Amain


**THIS IS ALPHA QUALITY, UNSUPPORTED, RUN AT YOUR OWN RISKS**

Your Tool For Python Performance Tracking


`perf8` is a curated list of tools to track the performance of your Python app.

The project will be pluggable, but also include a few opinionated wrappers to
make it easier to report performances.

I am including 3 plugins:

- perf8-gprof2dot - a cProfile to dot graph generator
- perf8-memray - a memory flamegraph generator
- perf8-psutil - a psutil integration

And they will all run using the same command (and off by default):

.. code-block:: sh

   perf8 --memray --psutil --gprof2dot /my/python/script.py

