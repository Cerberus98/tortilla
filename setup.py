#!/usr/bin/env python

import distutils.core

import pip.download
from pip.req import parse_requirements

try:
    import setuptools
except ImportError:
    pass

version = "0.01"


def requires(path):
    return [r.name for r in parse_requirements(path, session=pip.download.PipSession())
            if r]


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
        ]},
    install_requires=requires("requirements.txt"))
