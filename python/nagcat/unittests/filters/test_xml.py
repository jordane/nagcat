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
from nagcat import errors, filters

class XPathTestCase(unittest.TestCase):

    example = """
    <html>
        <head>
            <title>Test XML</title>
        </head>
        <body>
            <div class="title">This has been a test</div>
            <p>Text #1</p><p>Text #2</p>
        </body>
    </html>
    """

    def testBasic(self):
        f = filters.Filter(object(), "xpath://div/text()")
        self.assertEquals(f.filter(self.example), "This has been a test")

    def testMissing(self):
        f = filters.Filter(object(), "xpath://span/text()")
        self.assertIsInstance(f.filter(self.example), errors.Failure)

    def testDefault(self):
        f = filters.Filter(object(), "xpath[none]://span/text()")
        self.assertEquals(f.filter(self.example), "none")

    def testBad(self):
        f = filters.Filter(object(), "xpath://span/text()")
        self.assertIsInstance(f.filter("<foo></bar>"), errors.Failure)

    def testXML(self):
        f = filters.Filter(object(), "xpath://title")
        self.assertEquals(f.filter(self.example), "<title>Test XML</title>")

    def testMultiXML(self):
        f = filters.Filter(object(), "xpath://p")
        self.assertEquals(f.filter(self.example),
                "<p>Text #1</p>\n<p>Text #2</p>")
