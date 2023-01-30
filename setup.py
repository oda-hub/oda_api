#!/usr/bin/env python

from __future__ import absolute_import, division, print_function

from builtins import (bytes, str, open, super, range,
                      zip, round, input, int, pow, object, map, zip)

__author__ = 'andrea tramacere'


from setuptools import setup, find_packages
import glob
import json

packs=find_packages()

with open('oda_api/pkg_info.json') as fp:
    _info = json.load(fp)

__version__ = _info['version']


include_package_data=True

scripts_list=glob.glob('./bin/*')
setup(name='oda_api',
      version=__version__,
      description='API plugin  for CDCI online data analysis',
      author='Andrea Tramacere, Volodymyr Savchenko',
      author_email='contact@odahub.io',
      scripts=scripts_list,
      packages=packs,
      package_data={'oda_api': ['config_dir/*']},
      include_package_data=True,
      install_requires=[
            "requests",
            "future",
            "astropy>=3.2",
            "json_tricks",
            "matplotlib",
            "numpy",
            "jsonschema",
            "pyjwt",
            "astroquery",
            "scipy",
            "rdflib",
            "black"
        ],
      extras_require={
          'test': [
                "pytest-xdist[psutil]",
                "astroquery>=0.4.4",
                "sentry_sdk"
            ],      
          'extra-test': [
                "pytest-xdist[psutil]",
                "astroquery>=0.4.4",
            ],      
          'gw': [
            "gwpy",
            "ligo.skymap"
          ]
         },
      entry_points={
          "console_scripts": [
            "oda-api = oda_api.cli:main"
          ]
        },
      python_requires='>=2.7',
      )



