# Copyright 2019-2021 XMOS LIMITED.
# This Software is subject to the terms of the XMOS Public Licence: Version 1.
import setuptools

# Another repository might depend on python code defined in this one.  The
# procedure to set up a suitable python environment for that repository may
# pip-install this one as editable using this setup.py file.  To minimise the
# chance of version conflicts while ensuring a minimal degree of conformity,
# the 3rd-party modules listed here require the same major version and at
# least the same minor version as specified in the requirements.txt file.
# The same modules should appear in the requirements.txt file as given below.
setuptools.setup(
    name='audio_test_tools',
    packages=setuptools.find_packages(),
    install_requires=[
        'flake8~=4.0',
        'matplotlib~=3.5',
        'numpy~=1.21',
        'pandas~=1.3',
        'pylint~=2.13',
        'pytest~=7.1',
        'pytest-xdist~=2.5',
        'scipy~=1.7',
        'sh~=1.14',
    ],
    dependency_links=[
    ],
)
