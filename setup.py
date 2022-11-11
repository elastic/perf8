import sys
from setuptools import setup, find_packages

if sys.version_info < (3, 9):
    raise ValueError("Requires Python 3.9 or superior")

from perf8 import __version__  # NOQA

install_requires = ["psutil", "matplotlib", "flameprof", "memray"]


description = ""

for file_ in ("README", "CHANGELOG"):
    with open("%s.rst" % file_) as f:
        description += f.read() + "\n\n"


classifiers = [
    "Programming Language :: Python",
    "License :: OSI Approved :: Apache Software License",
    "Development Status :: 5 - Production/Stable",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
]


setup(
    name="perf8",
    version=__version__,
    url="https://pypi.org/project/perf8",
    packages=find_packages(),
    long_description=description.strip(),
    description=("Your Tool For Python Performance Tracking"),
    author="Tarek Ziade",
    author_email="tarek@ziade.org",
    include_package_data=True,
    zip_safe=False,
    classifiers=classifiers,
    install_requires=install_requires,
    entry_points="""
      [console_scripts]
      perf8 = perf8.run:main
      """,
)
