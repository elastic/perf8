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

data = []
RANGE = 100000


def get_random(min, max):
    return random.randint(min, max)


def math1(x, y):
    x * y


def math2(x, y):
    y**x


def do_math(x, y):
    math1(x, y)
    math2(x, y)


# generates one GiB in RSS
def main():
    for i in range(RANGE):
        data.append(get_random(1, 3722837687624) ** 4)
        data.append("r" * get_random(100, 20000))
        if get_random(1, 20) == 2:
            print(f"[{os.getpid()}] Busy adding data! ({i}/{RANGE})")
            try:
                do_math(i, RANGE)
            except Exception as e:
                print(e)


if __name__ == "__main__":
    main()
