#!/usr/bin/python

"""Copyright 2013 Google Inc. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


import re

import pinject


readme_contents = open('README.rst').read()
paragraphs = re.split('\n\n', readme_contents)
for index, paragraph in enumerate(paragraphs):
    if paragraph != '.. code-block:: python':
        continue
    snippet = paragraphs[index + 1]
    code_lines = [line[8:] for line in snippet.split('\n')
                  if line.startswith('    >>> ') or line.startswith('    ... ')]
    code = ''.join(line + '\n' for line in code_lines)
    exec code
