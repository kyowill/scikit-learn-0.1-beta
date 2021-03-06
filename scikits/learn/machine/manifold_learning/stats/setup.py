from os.path import join

import os.path
import numpy

def configuration(parent_package='', top_path=None, package_name='stats'):
    from numpy.distutils.misc_util import Configuration
    config = Configuration(package_name,parent_package,top_path)
    config.add_subpackage('*')
    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(**configuration(top_path='',
                          package_name='stats').todict())
    #setup(configuration=configuration)
