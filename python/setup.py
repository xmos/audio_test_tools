# Copyright (c) 2019, XMOS Ltd, All rights reserved
import setuptools

setuptools.setup(
    name='audio_test_tools',
    packages=setuptools.find_packages(),
    install_requires=[
        'flake8',
        'matplotlib',
        'numpy',
        'pandas',
        'pylint',
        'pytest',
        'pytest-xdist',
        'scipy',
    ]
)
