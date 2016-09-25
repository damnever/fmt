# -*- coding: utf-8 -*-

"""
f-strings(Python 3.6) style literal string interpolation.
Ref: https://www.python.org/dev/peps/pep-0498/
"""

from __future__ import absolute_import

import sys

from .fmt import Fmt


version = __version__ = '0.1.0'
version_info = [int(num) for num in version.split('.')]


# Install the Fmt() object in sys.modules,
# so that "import fmt" gives a callable fmt.
sys.modules['fmt'] = Fmt()
