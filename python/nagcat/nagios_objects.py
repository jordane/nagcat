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

"""Parsers for nagios config and object files"""

import re

# Note that this expects files generated *by* nagios
# such objects.cache or status.dat

class ObjectParser(object):
    """Parse a given config file for the requested objects"""

    def __init__(self, object_file, object_types=(), object_select={}):
        self._objects = {}
        for type_ in object_types:
            self._objects[type_] = []

        input = open(object_file)
        splitter = None
        object = None
        object_type = None
        try:
            for line in input:
                line = line.strip()
                if object is None:
                    if line.startswith("define") and line.endswith('{'):
                        type_ = line[7:-2]
                        splitter = None
                    elif line.endswith('status {'):
                        splitter = '='
                        type_ = line[:-8]
                    else:
                        continue

                    assert type_
                    if object_types and type_ not in object_types:
                        continue
                    object = {}
                    object_type = type_
                elif line == '}':
                    if object_type not in self._objects:
                        self._objects[object_type] = [object]
                    else:
                        self._objects[object_type].append(object)
                    object = None
                    object_type = None
                else:
                    split = line.split(splitter, 1)
                    key = split[0]

                    if len(split) == 2:
                        value = split[1].lstrip()
                    else:
                        value = ""

                    if object_select and key in object_select:
                        selector = object_select[key]
                        if isinstance(selector, basestring):
                            if value != selector:
                                object = None
                                object_type = None
                                continue
                        else:
                            if value not in selector:
                                object = None
                                object_type = None
                                continue

                    object[key] = value
        finally:
            input.close()

    def __getitem__(self, key):
        return self._objects[key]

    def __contains__(self, key):
        return key in self._objects

    def types(self):
        return self._objects.keys()

class ConfigParser(object):
    """Parser for the main nagios config file (nagios.cfg)"""

    ATTR = re.compile("^(\w+)\s*=\s*(.*)$")

    def __init__(self, config_file):

        self._config = {}

        config_fd = open(config_file)

        for line in config_fd:
            line = line.strip()
            match = self.ATTR.match(line)
            if match:
                self._config[match.group(1)] = match.group(2)

        config_fd.close()

    def __getitem__(self, key):
        return self._config[key]

    def __contains__(self, key):
        return key in self._config

    def keys(self):
        return self._config.keys()

if __name__ == "__main__":
    import sys, pprint
    assert len(sys.argv) == 2
    parser = Parser(sys.argv[1])
    for type_ in parser.types():
        print "### %s ###" % type_
        pprint.pprint(parser[type_])
