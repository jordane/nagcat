# Copyright 2008-2009 ITA Software, Inc.
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

from __future__ import division

"""Exceptions and configuration bits that are used everywhere"""

import re
from coil import struct

STATES = ["OK", "WARNING", "CRITICAL", "UNKNOWN"]

def applyTreeDefaults(struct, defaults):
    """Recursively add the attributes in defaults to each Struct.

    The root node has the values set in it while child nodes will
    simply link back to their parent. That way the defaults can
    be overridden on a per-subtree basis.
    """

    def childDefaults(struct):
        for key in defaultspy:
            struct.setdefault(key, struct.Link("..%s" % key, struct)


class Repeat(object):
    """Store a repeat time interval.

    A if initialized with None or '0 seconds' there is no repeat.
    """
    # TODO: support absolute times

    def __init__(self, value):
        if not value:
            # Default to no repeat
            self.seconds = 0.0
            return

        match = re.match("^\s*(\d+(\.\d+)?)\s*"
                "(s|sec|seconds?|m|min|minutes?|h|hours?)\s*$",
                str(value), re.IGNORECASE)
        if not match:
            raise KnownError("Invalid repeat interval '%s'" % str(value))

        if match.group(3)[0].lower() == 's':
            self.seconds = float(match.group(1))
        elif match.group(3)[0].lower() == 'm':
            self.seconds = float(match.group(1)) * 60
        elif match.group(3)[0].lower() == 'h':
            self.seconds = float(match.group(1)) * 3600
        else:
            assert(0)

    def __str__(self):
        return "%s seconds" % self.seconds

    def __nonzero__(self):
        return bool(self.seconds)

    def __eq__(self, other):
        if (isinstance(other, self.__class__) and
                self.seconds == other.seconds):
            return True
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)


class MathString(str):
    """A string that supports numeric operations.

    This allows evaluations done on test results to not have to worry
    about casting between string and number types by behaving like a
    number for for all standard math operations. Of course if the user
    wants to run a stringified math operation such as "foo"+"bar" they
    will have to cast using str() first. But in the case of the +
    operator "%s" % foo style syntax is usually much better anyway.

    The following operators are computed as a number:

        + - * / // % divmod() pow() ** < <= >= >

    Use of these operators on any non-numeric value will raise a KnownError

    The == and != operators will do a numeric comparison if the two
    values happen to be numbers, otherwise it will compare them as
    strings.
    """

    def __digify_args(*args):
        """Covert all arguments to a number"""

        numbers = []

        for arg in args:
            if isinstance(arg, MathString):
                if '.' in arg:
                    numtype = float
                else:
                    numtype = int

                try:
                    arg = numtype(arg)
                except ValueError:
                    raise KnownError("Attempted math on a string!",
                            arg, "CRITICAL")

            numbers.append(arg)

        return numbers

    def __float__(self):
        return float(str(self))

    def __int__(self):
        try:
            return int(str(self))
        except ValueError:
            return int(float(self))

    def __long__(self):
        try:
            return long(str(self))
        except ValueError:
            return long(float(self))

    def __add__(self, other):
        nself, nother = self.__digify_args(other)
        return nself + nother

    def __radd__(self, other):
        nself, nother = self.__digify_args(other)
        return nother + nself

    def __sub__(self, other):
        nself, nother = self.__digify_args(other)
        return nself - nother

    def __rsub__(self, other):
        nself, nother = self.__digify_args(other)
        return nother - nself

    def __mul__(self, other):
        nself, nother = self.__digify_args(other)
        return nself * nother

    def __rmul__(self, other):
        nself, nother = self.__digify_args(other)
        return nother * nself

    def __truediv__(self, other):
        nself, nother = self.__digify_args(other)
        return nself / nother

    def __rtruediv__(self, other):
        nself, nother = self.__digify_args(other)
        return nother / nself

    def __floordiv__(self, other):
        nself, nother = self.__digify_args(other)
        return nself // nother

    def __rfloordiv__(self, other):
        nself, nother = self.__digify_args(other)
        return nother // nself

    def __mod__(self, other):
        nself, nother = self.__digify_args(other)
        return nself % nother

    def __rmod__(self, other):
        nself, nother = self.__digify_args(other)
        return nother % nself

    def __divmod__(self, other):
        nself, nother = self.__digify_args(other)
        return divmod(nself, nother)

    def __rdivmod__(self, other):
        nself, nother = self.__digify_args(other)
        return divmod(nother, nself)

    def __pow__(self, other, mod=None):
        if mod is None:
            nself, nother = self.__digify_args(other)
            return nself ** nother
        else:
            nself, nother, nmod = self.__digify_args(other, mod)
            return pow(nself, nother, nmod)

    def __rpow__(self, other):
        nself, nother = self.__digify_args(other)
        return nother ** nself

    def __neg__(self):
        nself, = self.__digify_args()
        return -nself

    def __abs__(self):
        nself, = self.__digify_args()
        return abs(nself)

    def __lt__(self, other):
        nself, nother = self.__digify_args(other)
        return nself < nother

    def __le__(self, other):
        nself, nother = self.__digify_args(other)
        return nself <= nother

    def __gt__(self, other):
        nself, nother = self.__digify_args(other)
        return nself > nother

    def __ge__(self, other):
        nself, nother = self.__digify_args(other)
        return nself >= nother

    def __eq__(self, other):
        try:
            nself, nother = self.__digify_args(other)
            ret = nself == nother
        except KnownError:
            ret = str.__eq__(self, other)

        return ret

    def __ne__(self, other):
        return not self.__eq__(other)


class KnownError(Exception):
    """Records a test failure and the output at that time.

    Any failure or exception that may be caused by either a bad config
    or a failed test should be represented by this class with result and
    state set to provide good diagnostic data in the generated report.
    """

    def __init__(self, msg, result="", state="UNKNOWN", error=""):
        Exception.__init__(self, msg)
        self.result = result

        assert state in STATES
        self.state = state

        if error:
            self.error = error
        else:
            self.error = msg

class InitError(Exception):
    """Fatal errors during startup."""
    pass