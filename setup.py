# -*- coding: utf-8 -*-

# flake8: noqa: F401, F601
import os

from pip._internal.req import parse_requirements
from setuptools import find_packages, setup

__copyright__ = (
    "Flensburg University of Applied Sciences, "
    "Europa-Universität Flensburg, "
    "Centre for Sustainable Energy Systems"
)
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "wolf_bunke, maltesc"


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


req = []

dev_req = [
    "pre-commit",
    "black",
    "isort",
    "pyupgrade",
    "flake8",
]

doc_req = ["numpydoc", "sphinxcontrib.httpdomain", "sphinx-jsondomain"]

full_req = list(set(dev_req + doc_req))

extras = {
    "dev": dev_req,
    "doc": doc_req,
    "full": full_req,
}


setup(
    name="eGo",
    version="0.3.4",
    author="wolfbunke, maltesc",
    author_email="wolf-dieter.bunke@uni-flensburg.de",
    description=("A cross-grid-level electricity grid and storage optimization tool."),
    long_description=read("README.rst"),
    url="https://github.com/openego/eGo",
    license="GNU Affero General Public License Version 3 (AGPL-3.0)",
    packages=find_packages(),
    package_dir={"ego": "ego"},
    include_package_data=True,
    install_requires=req,
    extras_require=extras,
    package_data={
        "ego": [os.path.join("tools", "*.json")] + [os.path.join("", "*.json")],
    },
)
