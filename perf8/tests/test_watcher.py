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
import os
import pytest
import shutil
import tempfile

from perf8.watcher import WatchedProcess


@pytest.mark.asyncio
async def test_watcher():
    os.environ["RANGE"] = "1000"

    class Args:
        command = os.path.join(os.path.dirname(__file__), "demo.py")
        refresh_rate = 0.1
        psutil = True
        cprofile = True
        memray = False
        asyncstats = False
        pyspy = False
        target_dir = tempfile.mkdtemp()
        verbose = 2

    try:
        watcher = WatchedProcess(Args())

        await watcher.run()
        assert os.path.exists(os.path.join(Args.target_dir, "index.html"))
    finally:
        shutil.rmtree(Args.target_dir)


@pytest.mark.asyncio
async def test_async_watcher():
    os.environ["RANGE"] = "1000"

    class Args:
        command = os.path.join(os.path.dirname(__file__), "ademo.py")
        refresh_rate = 0.1
        psutil = True
        cprofile = False
        memray = True
        asyncstats = True
        pyspy = False
        target_dir = tempfile.mkdtemp()
        verbose = 2

    try:
        watcher = WatchedProcess(Args())

        await watcher.run()
        assert os.path.exists(os.path.join(Args.target_dir, "index.html"))
    finally:
        shutil.rmtree(Args.target_dir)
