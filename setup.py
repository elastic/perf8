#
# Licensed to Elasticsearch B.V. under one or more contributor
# license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright
# ownership. Elasticsearch B.V. licenses this file to you under
# the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#	http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
import sys
import re
from setuptools import setup, find_packages

if sys.version_info < (3, 9):
    raise ValueError("Requires Python 3.9 or superior")

from perf8 import __version__  # NOQA

install_requires = []
with open("requirements.txt") as f:
    reqs = f.readlines()
    for req in reqs:
        req = req.strip()
        if req == "" or req.startswith("#"):
            continue
        requirement = re.split(">|=", req)[0]
        install_requires.append(requirement)


description = ""

for file_ in ("README", "CHANGELOG"):
    with open("%s.rst" % file_) as f:
        description += f.read() + "\n\n"


classifiers = [
    "Programming Language :: Python",
    "License :: OSI Approved :: Apache Software License",
    "Development Status :: 5 - Production/Stable",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11"
]


setup(
    name="perf8",
    version=__version__,
    url="https://github.com/elastic/perf8",
    packages=find_packages(),
    long_description=description.strip(),
    description=("Your Tool For Python Performance Tracking"),
    author="Ingestion Team",
    author_email="tarek@ziade.org",
    include_package_data=True,
    zip_safe=False,
    classifiers=classifiers,
    install_requires=install_requires,
    entry_points="""
      [console_scripts]
      perf8 = perf8.cli:main
      """,
)
