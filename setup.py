#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import setup, find_namespace_packages
import os

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "docker-lets-network",
    version = read("VERSION"),
    license = "gpl-3.0",
    description = "lets modules for networking",
    long_description = read("README.md"),
    long_description_content_type = "text/markdown",
    author = "johneiser",
    url = "https://github.com/johneiser/lets_network",
    # download_url = "https://github.com/johneiser/lets_network/releases",
    packages = find_namespace_packages(include=[
        "lets.*"
    ]),
    keywords = [
        "lets",
        "docker",
        "framework",
    ],
    python_requires = ">=3.5.0",
    install_requires = [
        "docker-lets>=3.0.7",
        "pyopenssl",
        "scapy",
    ],
    classifiers = [
        "Development Status :: 3 - Alpha",
        # "Development Status :: 4 - Beta",
        # "Development Status :: 5 - Production / Stable",

        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    entry_points = {
        "lets" : [
            "modules=lets:.",
        ],
    }
)
