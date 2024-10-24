from setuptools import setup
import json

with open('oda_api/pkg_info.json') as fp:
    _info = json.load(fp)

__version__ = _info['version']

setup(
    version=__version__,
    setup_requires=['setuptools'],
)
