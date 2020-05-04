

from __future__ import absolute_import, division, print_function


import pkgutil
import os
import json

__author__ = "Andrea Tramacere"

with open(os.path.dirname(__file__) + '/pkg_info.json') as fp:
    _info = json.load(fp)


pkg_dir = os.path.abspath(os.path.dirname(__file__))
pkg_name = os.path.basename(pkg_dir)

__version__=_info['version']

__all__=[]
for importer, modname, ispkg in pkgutil.walk_packages(path=[pkg_dir],
                                                      prefix=pkg_name+'.',
                                                      onerror=lambda x: None):

    if ispkg == True:
        __all__.append(modname)
    else:
        pass



conf_dir=os.path.dirname(__file__)+'/config_dir'

env_phat=os.environ.get('CDCI_API_PLUGIN_CONF_FILE')

if env_phat is not None:
    conf_dir=env_phat

conf_file=os.path.join(conf_dir,'data_server_conf.yml')


