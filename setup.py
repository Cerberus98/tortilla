#!/usr/bin/env python

import sys
import distutils.core

try:
    import setuptools
except ImportError:
    pass

version = "0.01"


distutils.core.setup(
    name="tortilla",
    version=version,
    packages=["tortilla"],
    author="Matt Dietz",
    author_email="matthew.dietz@gmail.com",
    url="",
    download_url="",
    license="Apache 2",
    description="",
    entry_points={
        "tortilla.config": [
            "foo = tortilla.poo:foo",
        ],
        "console_scripts": [
            "foo = bar"
        ]}
    )
