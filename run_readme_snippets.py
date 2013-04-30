#!/usr/bin/python

import pinject
import re

readme_contents = open('README').read()
snippets = re.split(r'{{{([^}]+)}}}', readme_contents)[1::2]
for snippet in snippets:
    code_lines = [line[4:] for line in snippet.split('\n')
                  if line.startswith('>>> ') or line.startswith('... ')]
    code = ''.join(line + '\n' for line in code_lines)
    #eval(code)
    exec code
