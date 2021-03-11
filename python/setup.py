# Copyright (c) 2019-2021, XMOS Ltd, All rights reserved
# This software is available under the terms provided in LICENSE.txt.
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
        'flake8~=3.8',
        'matplotlib~=3.3',
        'numpy~=1.18',
        'pandas~=1.1',
        'pylint~=2.5',
        'pytest~=6.0',
        'pytest-xdist~=1.34',
        'scipy~=1.4',
        'sh~=1.13',
    ],
    dependency_links=[
    ],
)
