import os
from setuptools import setup, find_packages, Command

from evillimiter import __version__, __description__


class CleanCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        os.system('rm -vrf ./build ./dist ./*.pyc ./*.pyo ./*.pyd ./*.tgz ./*.egg-info `find -type d -name __pycache__`')


NAME = 'evillimiter'
AUTHOR = 'bitbrute'
AUTHOR_EMAIL = 'bitbrute@gmail.com'
LICENSE = 'MIT'
VERSION = __version__
URL = 'https://github.com/bitbrute/evillimiter'
DESCRIPTION = __description__
KEYWORDS = ["evillimiter", "limit", "bandwidth", "network"]
PACKAGES = find_packages()
INCLUDE_PACKAGE_DATA = True

CLASSIFIERS = ['Development Status :: 3 - Alpha',
               'Environment :: Console',
               'Intended Audience :: End Users/Desktop',
               'Intended Audience :: System Administrators',
               'Intended Audience :: Developers',
               'License :: OSI Approved :: MIT License',
               'Natural Language :: English',
               'Operating System :: Unix',
               'Programming Language :: Python :: 3.7',
               'Programming Language :: Python :: 3 :: Only',
               'Topic :: System :: Networking',
               ]

PYTHON_REQUIRES = '>= 3'
ENTRY_POINTS = { 'console_scripts': ['evillimiter = evillimiter.evillimiter:run'] }

INSTALL_REQUIRES = ['colorama',
                    'netaddr',
                    'netifaces',
                    'tqdm',
                    'scapy',
                    'terminaltables'
                    ]

CMDCLASS = { 'clean': CleanCommand }


setup(
    name=NAME,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    license=LICENSE,
    keywords=KEYWORDS,
    packages=PACKAGES,
    include_package_data=INCLUDE_PACKAGE_DATA,
    version=VERSION,
    python_requires=PYTHON_REQUIRES,
    entry_points=ENTRY_POINTS,
    install_requires=INSTALL_REQUIRES,
    classifiers=CLASSIFIERS,
    url=URL,
    cmdclass=CMDCLASS,
)