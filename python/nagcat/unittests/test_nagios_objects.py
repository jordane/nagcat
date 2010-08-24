# Copyright 2010 ITA Software, Inc.
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
from nagcat import nagios_objects, _object_parser_py

try:
    from nagcat import _object_parser_c
except ImportError:
    _object_parser_c = None


class ModuleTestcase(unittest.TestCase):

    def testObjectParser(self):
        expect = [_object_parser_py.ObjectParser]
        if _object_parser_c:
            expect.append(_object_parser_c.ObjectParser)
        self.assertIn(nagios_objects.ObjectParser, expect)

class ObjectsPyTestCase(unittest.TestCase):

    objects = {
            'host': [
                {
                    'host_name': 'host1',
                    'alias': 'Host 1',
                },
            ],
            'service': [
                {
                    'service_description': "Service 1",
                    'host_name': 'host1',
                },
            ],
        }

    parser = _object_parser_py.ObjectParser

    def mkfile(self):
        file_path = self.mktemp()
        file_obj = open(file_path, 'w')
        for obj_type, seq in self.objects.iteritems():
            file_obj.write("define %s {\n" % obj_type)
            for obj in seq:
                for attr, value in obj.iteritems():
                    file_obj.write("    %s %s\n" % (attr, value))
            file_obj.write("    }\n")
        file_obj.close()
        return file_path

    def testSimple(self):
        parser = self.parser(self.mkfile())
        parsed = dict((k,parser[k]) for k in parser.types())
        self.assertEquals(parsed, self.objects)

class StatusPyTestCase(unittest.TestCase):

    objects = {
            'host': [
                {
                    'host_name': 'host1',
                    'alias': 'Host 1',
                },
            ],
            'service': [
                {
                    'service_description': "Service 1",
                    'host_name': 'host1',
                },
            ],
        }

    parser = _object_parser_py.ObjectParser

    def mkfile(self):
        file_path = self.mktemp()
        file_obj = open(file_path, 'w')
        for obj_type, seq in self.objects.iteritems():
            file_obj.write("%sstatus {\n" % obj_type)
            for obj in seq:
                for attr, value in obj.iteritems():
                    file_obj.write("    %s=%s\n" % (attr, value))
            file_obj.write("    }\n")
        file_obj.close()
        return file_path

    def testSimple(self):
        parser = self.parser(self.mkfile())
        parsed = dict((k,parser[k]) for k in parser.types())
        self.assertEquals(parsed, self.objects)

class ObjectsCTestCase(ObjectsPyTestCase):
    if _object_parser_c:
        parser = _object_parser_c.ObjectParser
    else:
        skip = "C module missing"

class StatusCTestCase(StatusPyTestCase):
    if _object_parser_c:
        parser = _object_parser_c.ObjectParser
    else:
        skip = "C module missing"
