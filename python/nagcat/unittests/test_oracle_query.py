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

import os
from twisted.trial import unittest
from nagcat import errors, query, plugin
from coil.struct import Struct

# NOTE: user/pw/sid are not included here, for security reasons.  Please set the
# following environment variables accordingly when running this test:
# ORA_USER, ORA_PASS, ORA_DSN
class OracleTestCase(unittest.TestCase):
    try:
        import cx_Oracle, lxml
    except ImportError:
        skip = "Missing cx_Oracle or lxml"

    def setUp(self):

        if ('ORA_DSN' in os.environ and
            'ORA_USER' in os.environ and
            'ORA_PASS' in os.environ):

            self.config = Struct({'user':os.environ['ORA_USER'],
                                  'password':os.environ['ORA_PASS'],
                                  'dsn':os.environ['ORA_DSN'],
                                  'sql':'select 1 as data from dual'})
        else:
            raise unittest.SkipTest("Missing oracle credentials")

    def testSimple(self):
        conf = self.config.copy()
        conf['sql'] = 'select 1 as data from dual'

        qcls = plugin.search(query.IQuery, "oraclesql")
        q = qcls(conf)
        d = q.start()
        d.addBoth(self.endSimple, q)
        return d

    def endSimple(self, ignore, q):
        expected = ('<queryresult><row>'
                        '<data type="NUMBER">1</data>'
                    '</row></queryresult>')
        self.assertEquals(q.result, expected)

    def testBadQuery(self):
        raise unittest.SkipTest("Not working yet")

        conf = self.config.copy()
        conf['sql'] = 'select 1 from dual'

        qcls = plugin.search(query.IQuery, "oraclesql")
        q = qcls(conf)
        d = q.start()
        d.addBoth(self.endBadQuery, q)
        return d

    def endBadQuery(self, ignore, q):
        self.assertIsInstance(q.result, errors.Failure)


class OracleBadLoginTestCase(unittest.TestCase):
    try:
        import cx_Oracle, lxml
    except ImportError:
        skip = "Missing cx_Oracle or lxml"

    def setUp(self):
        self.config = Struct({'user':'baduser', 
                              'password':'pw', 
                              'dsn':'nodb',
                              'sql':'select 1 from dual'})

    def testBadQuery(self):
        qcls = plugin.search(query.IQuery, "oraclesql")
        q = qcls(self.config)
        d = q.start()
        d.addBoth(self.endBadQuery, q)
        return d

    def endBadQuery(self, ignore, q):
        self.assertIsInstance(q.result, errors.Failure)

