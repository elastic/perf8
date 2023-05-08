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

"""
Demo script to test perf8
"""
import random
import os
import tempfile
import shutil
import string
import statsd
import time

data = []
RANGE = int(os.environ.get("RANGE", 50000))


def get_random(min, max):
    return random.randint(min, max)


def math1(x, y):
    x * y


def math2(x, y):
    y**x


def do_math(x, y):
    math1(x, y)
    math2(x, y)


def add_mem1():
    data.append("r" * get_random(100, 2000))


def add_mem2(tempdir):
    data.append("r" * get_random(100, 2000))
    add_mem3()
    name = "".join(random.choice(string.ascii_lowercase) for i in range(10))
    with open(os.path.join(tempdir, name), "w") as f:
        f.write("data" * get_random(100, 2000))


def add_mem3():
    data.append("r" * get_random(100, 20000))


# generates one GiB in RSS
def main():
    time.sleep(2)
    tempdir = tempfile.mkdtemp()
    c = statsd.StatsClient("localhost", 514)

    for i in range(RANGE):
        c.incr("cycle")
        add_mem1()
        add_mem2(tempdir)

        if get_random(1, 20) == 2:
            print(f"[{os.getpid()}] Busy adding data! ({i}/{RANGE})")
            try:
                do_math(i, RANGE)
            except Exception as e:
                print(e)

    shutil.rmtree(tempdir)


if __name__ == "__main__":
    main()
    print("Bye!")
