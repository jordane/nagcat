# Copyright 2009 ITA Software, Inc.
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
#from nagcat.unittests import dummy_server
from coil.struct import Struct
from nagcat import base, scheduler


class SchedulerTestCase(unittest.TestCase):

    def testSimpleGrouping(self):
        r1 = scheduler.Runnable(Struct({'repeat': 60}))
        r2 = scheduler.Runnable(Struct({'repeat': 60}))
        r3 = scheduler.Runnable(Struct({'repeat': 60}))
        t1 = scheduler.Runnable(Struct({'repeat': 60}))
        t1.addDependency(r1)
        t1.addDependency(r2)
        t2 = scheduler.Runnable(Struct({'repeat': 60}))
        t2.addDependency(r2)
        t3 = scheduler.Runnable(Struct({'repeat': 60}))
        t3.addDependency(r3)
        s = scheduler.Scheduler(base.NagcatDummy())
        s.register(t1)
        s.register(t2)
        s.register(t3)
        s.prepare()
        stats = s.stats()
        expect = {'count': 8,
                  'Test': {'count': 0},
                  'Runnable': {'count': 6},
                  'Group': {'count': 2},
                  'Query': {'count': 0}}
        self.assertEquals(stats['tasks'], expect)

class RunnableTestCase(unittest.TestCase):

    def testSingle(self):
        r = scheduler.Runnable(Struct({'repeat': None}))
        d = r.start()
        d.addBoth(self.endSingle, r)
        return d

    def endSingle(self, ignore, r):
        self.assertIdentical(r.result, None)
