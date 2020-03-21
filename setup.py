#!/usr/bin/env python
#
# Copyright 2013 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from setuptools import setup
import semver


def versioning(version: str) -> str:
    """
    version to specification
    Author: Huan <zixia@zixia.net> (https://github.com/huan)

    X.Y.Z -> X.Y.devZ

    """
    sem_ver = semver.parse(version)

    major = sem_ver['major']
    minor = sem_ver['minor']
    patch = str(sem_ver['patch'])

    if minor % 2:
        patch = 'dev' + patch

    fin_ver = '%d.%d.%s' % (
        major,
        minor,
        patch,
    )

    return fin_ver


# Extra __version__ from VERSION instead of pinject.version so pip doen't
# import __init__.py and bump into dependencies that haven't been installed
# yet.
def get_version() -> str:
    """
    read version from VERSION file
    """
    version = '0.0.0'

    with open(
            os.path.join(
                os.path.dirname(__file__),
                'VERSION'
            )
    ) as handle:
        # Get X.Y.Z
        version = handle.read().strip()
        # versioning from X.Y.Z to X.Y.devZ
        version = versioning(version)

    return version


setup(
    name='pinject',
    version=get_version(),
    description='A pythonic dependency injection library',
    author='Kurt Steinkraus',
    author_email='kurt@steinkraus.us',
    url='https://github.com/google/pinject',
    license='Apache License 2.0',
    long_description=open('README.rst').read(),
    platforms='all',
    packages=['pinject'],
    install_requires=['six>=1.7.3', 'decorator>=4.3.0'],
)
