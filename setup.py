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

# Extra __version__ from VERSION instead of pinject.version so pip doen't
# import __init__.py and bump into dependencies that haven't been installed
# yet.
with open(os.path.join(os.path.dirname(__file__), "VERSION")) as VERSION:
    __version__ = VERSION.read().strip()

setup(name='pinject',
      version=__version__,
      description='A pythonic dependency injection library',
      author='Kurt Steinkraus',
      author_email='kurt@steinkraus.us',
      url='https://github.com/google/pinject',
      license='Apache License 2.0',
      long_description=open('README.rst').read(),
      platforms='all',
      packages=['pinject'],
      install_requires=['six>=1.7.3', 'decorator>=4.3.0'])
