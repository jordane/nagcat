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
import time
import subprocess

from twisted.python import log
from twisted.trial import unittest
from nagcat import errors, query, plugin
from coil.struct import Struct

try:
    import cx_Oracle
    from lxml import etree
except ImportError:
    cx_Oracle = None
    etree = None

class OracleBase(unittest.TestCase):
    if not cx_Oracle or not etree:
        skip = "Missing cx_Oracle or lxml"
    elif not ('ORA_DSN' in os.environ and
              'ORA_USER' in os.environ and
              'ORA_PASS' in os.environ):
        skip = "Missing oracle credentials"

    SQL_SETUP = ()
    SQL_CLEAN = ()

    QUERY_TYPE = "oracle_sql"

    def setUp(self):
        self.config = Struct({'user':os.environ['ORA_USER'],
                              'password':os.environ['ORA_PASS'],
                              'dsn':os.environ['ORA_DSN']})
        if self.SQL_SETUP:
            self.execute(self.SQL_SETUP)

    def tearDown(self):
        if self.SQL_CLEAN:
            self.execute(self.SQL_CLEAN)

    def execute(self, sqlseq):
        conn = cx_Oracle.Connection(user=self.config['user'],
                                    password=self.config['password'],
                                    dsn=self.config['dsn'],
                                    threaded=True)
        cursor = conn.cursor()
        for sql in sqlseq:
            try:
                cursor.execute(sql)
            except cx_Oracle.DatabaseError, ex:
                raise Exception("%s: %s" % (ex, sql))
        cursor.close()
        conn.close()

    def startQuery(self, **kwargs):
        conf = self.config.copy()
        conf.update(kwargs)
        qcls = plugin.search(query.IQuery, self.QUERY_TYPE)
        q = qcls(conf)
        d = q.start()
        d.addCallback(lambda x: q.result)
        return d

    def assertEqualsXML(self, result, expect):
        # Parse the xml, strip white space, and convert back
        # this allows us to compare if they are logically equal
        parser = etree.XMLParser(remove_blank_text=True)
        result = etree.tostring(etree.XML(result, parser))
        expect = etree.tostring(etree.XML(expect, parser))
        self.assertEquals(result, expect)

class SimpleTestCase(OracleBase):

    def testSimple(self):
        def check(result):
            self.assertEqualsXML(result, (
                '<queryresult><row>'
                    '<data type="NUMBER">1</data>'
                '</row></queryresult>'))

        d = self.startQuery(sql='select 1 as data from dual')
        d.addCallback(check)
        return d

    def testBinds(self):
        def check(result):
            self.assertEqualsXML(result, (
                '<queryresult><row>'
                    '<data type="NUMBER">1</data>'
                '</row></queryresult>'))

        d = self.startQuery(
                sql='select :blah as data from dual',
                binds=[1])
        d.addCallback(check)
        return d

    def testParams1(self):
        def check(result):
            self.assertEqualsXML(result, (
                '<queryresult><row>'
                    '<data type="NUMBER">2</data>'
                '</row></queryresult>'))

        d = self.startQuery(
                sql='select :blah as data from dual',
                parameters=[2])
        d.addCallback(check)
        return d

    def testParams2(self):
        def check(result):
            self.assertEqualsXML(result, (
                '<queryresult><row>'
                    '<data type="NUMBER">2</data>'
                '</row></queryresult>'))

        d = self.startQuery(
                sql='select :blah as data from dual',
                parameters=Struct({'blah': 2}))
        d.addCallback(check)
        return d

    def testString(self):
        def check(result):
            self.assertEqualsXML(result, (
                '<queryresult><row>'
                    '<data type="FIXED_CHAR">foo</data>'
                '</row></queryresult>'))

        d = self.startQuery(sql="select 'foo' as data from dual")
        d.addCallback(check)
        return d

    def testBadQuery(self):
        def check(result):
            self.assertIsInstance(result, errors.Failure)
        d = self.startQuery(sql='select 1')
        d.addBoth(check)
        return d

    def testBadUser(self):
        def check(result):
            self.assertIsInstance(result, errors.Failure)
        d = self.startQuery(sql='select 1 from dual', user='baduser')
        d.addBoth(check)
        return d

class DataTestCase(OracleBase):

    SQL_SETUP = (
        "create table test (a number, b varchar2(10))",
        "insert into test values (1, 'aaa')",
        "insert into test values (2, 'bbb')",
        "insert into test values (3, 'ccc')",
        "insert into test values (4, 'ddd')",
        "insert into test values (5, 'eee')",
        "commit")

    SQL_CLEAN = ("drop table test", "commit")

    def testSelectAll(self):
        def check(result):
            self.assertEqualsXML(result, """<queryresult>
                <row><a type="NUMBER">1</a><b type="STRING">aaa</b></row>
                <row><a type="NUMBER">2</a><b type="STRING">bbb</b></row>
                <row><a type="NUMBER">3</a><b type="STRING">ccc</b></row>
                <row><a type="NUMBER">4</a><b type="STRING">ddd</b></row>
                <row><a type="NUMBER">5</a><b type="STRING">eee</b></row>
            </queryresult>""")

        d = self.startQuery(sql='select * from test')
        d.addCallback(check)
        return d

    def testSelectCount(self):
        def check(result):
            self.assertEqualsXML(result, """<queryresult>
                <row><count type="NUMBER">5</count></row>
            </queryresult>""")

        d = self.startQuery(sql='select count(*) from test')
        d.addCallback(check)
        return d

def _read_sql(name):
    path = "%s/%s" % (os.path.dirname(os.path.abspath(__file__)), name)
    fd = open(path)
    try:
        text = fd.read()
    finally:
        fd.close()

    # Remove the trailing ; and / characters.
    # They are required for sqlplus, not us.
    #return text.rstrip("\n\t ;/").replace('\n', ' ')
    return text

class PLSQLTestCase(OracleBase):

    SQL_CLEAN = ("drop package pltest", "commit")

    QUERY_TYPE = "oracle_plsql"

    def setUp(self):
        super(PLSQLTestCase, self).setUp()

        sql = ""
        for path in ("test_oracle_ps.sql", "test_oracle_pb.sql"):
            path = "%s/%s" % (os.path.dirname(
                os.path.abspath(__file__)), path)
            fd = open(path)
            sql += fd.read()
            fd.close()

        # For some reason running this SQL via cx_Oracle doesn't
        # work, but it does with sqlplus. I don't know why. :-(
        proc = subprocess.Popen(
            ["sqlplus", "-S", "-L", "%s/%s@%s" % (
                self.config['user'],
                self.config['password'],
                self.config['dsn'])],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)

        out,bleh = proc.communicate(sql)
        for line in out.splitlines():
            line = line.strip()
            if line:
                log.msg("[sqlplus] %s" % line)

        assert proc.returncode == 0

    def test1(self):
        def check(result):
            xml = etree.fromstring(result)
            value = float(xml.find("p_out").text)
            # The value should be the current time but not quite
            # because the test package doesn't account for timezones
            # so as long as it is within 25 hours we'll call it good.
            self.assertApproximates(value, time.time(), 3600*25)

        d = self.startQuery(procedure="pltest.one",
                parameters=[['out', 'p_out', "number"]])
        d.addCallback(check)
        return d

    def test2(self):
        def check(result):
            self.assertEqualsXML(result, """<result>
                <p_out type="NUMBER">3.0</p_out>
            </result>""")

        d = self.startQuery(procedure="pltest.two",
                parameters=[['in', 'p_in', 7],
                    ['out', 'p_out', 'number']])
        d.addCallback(check)
        return d
