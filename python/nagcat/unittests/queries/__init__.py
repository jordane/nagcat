# Copyright 2009-2010 ITA Software, Inc.
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

from twisted.trial import unittest
from coil.struct import Struct
from nagcat import simple

class QueryTestCase(unittest.TestCase):

    def setUp(self):
        self.nagcat = simple.NagcatDummy()

    def startQuery(self, config=None, **kwargs):
        q,d = self.startQuery2(config=config, **kwargs)
        return d

    def startQuery2(self, config=None, **kwargs):
        if config:
            config = config.copy()
            config.update(kwargs)
        else:
            config = kwargs

        q = self.nagcat.new_query(Struct(config))
        d = q.start()
        d.addCallback(lambda x: q.result)
        return q,d
