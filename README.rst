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


Running and publishing using Github
-----------------------------------

You can use Github Actions and Github Pages to run and publish a performance report. In your project,
add a `.github/wokflows/perf.yml` file with this content:

.. code-block:: yaml

    ---
    name: Perf report demo
    on:
      workflow_dispatch:

    permissions:
      contents: read
      pages: write
      id-token: write

    jobs:
      build:
        runs-on: ubuntu-latest
        strategy:
          matrix:
            python-version:
              - '3.10'
          fail-fast: false
        name: Performance report using Python ${{ matrix.python-version }}
        steps:
          - uses: actions/checkout@v3

          - name: Setup Python
            uses: actions/setup-python@v4
            with:
              python-version: ${{ matrix.python-version }}

          - name: Install dot
            run: sudo apt-get install graphviz -y

          - name: Install perf8
            run: pip3 install perf8

          - name: Run Perf test
            run: perf8 --all

          - name: Setup GitHub Pages
            id: pages
            uses: actions/configure-pages@v1

          - name: Upload pages artifact
            uses: actions/upload-pages-artifact@v1
            with:
              path: /home/runner/work/perf8/perf8/perf8-report

          - name: Deploy to GitHub Pages
            id: deployment
            uses: actions/deploy-pages@v1


And extend `perf8 --all` so it runs your app. You will also need to go in the settings of your project and
the `Pages` page to switch to `GitHub Actions` for the `Build And Deployement` source.

When the action runs, it will update `https://<organization>.github.io/<project>`



Screencast
----------

.. image:: docs/perf8-screencast.gif
