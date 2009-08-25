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

import re

try:
    from lxml import etree
except ImportError:
    etree = None

from twisted.web import resource, server

from nagcat import errors

class XMLPage(resource.Resource):
    """Generic XML Page"""

    isLeaf = True

    def xml(self):
        """The XML representation of this page.

        Returns an etree.Element object.
        """
        raise Exception("Not Implemented")

    def render_GET(self, request):
        """Transform the xml to text and send it"""
        return etree.tostring(self.xml(), pretty_print=True)

class Ping(XMLPage):
    """Minimal alive page"""

    def xml(self):
        return etree.Element("ok", version="1.0")

class Memory(XMLPage):
    """Process memory usage"""

    vm_regex = re.compile("^(Vm\w+):\s+(\d+)\s+(\w+)$")

    def xml(self):
        mem = etree.Element("Memory", version="1.0")

        status = open("/proc/self/status")
        for line in status:
            match = self.vm_regex.match(line)
            if not match:
                continue
            new = etree.SubElement(mem, match.group(1), units=match.group(3))
            new.text = match.group(2)

        status.close()
        return mem

class Scheduler(XMLPage):
    """Information on objects in the Nagcat scheduler"""

    def __init__(self, scheduler):
        XMLPage.__init__(self)
        self.scheduler = scheduler

    def xml(self):
        sch = etree.Element("Scheduler", version="1.0")

        data = self.scheduler.stats()

        lat = etree.SubElement(sch, "Latency",
                period=str(data['latency']['period']))
        etree.SubElement(lat, "Maximum").text = "%f" % data['latency']['max']
        etree.SubElement(lat, "Minimum").text = "%f" % data['latency']['min']
        etree.SubElement(lat, "Average").text = "%f" % data['latency']['avg']

        tasks = etree.SubElement(sch, 'Tasks')
        etree.SubElement(tasks, "Groups").text = str(data['tasks']['groups'])

        return sch

class Stat(XMLPage):
    """The main /stat page"""

    isLeaf = False

    def __init__(self):
        XMLPage.__init__(self)

        # self.children is a dict but we want the order to be
        # predictable to avoid surprising people using this page.
        self.order = []

        self.putChild("", self)
        self.putChild("ping", Ping())
        self.putChild("memory", Memory())

    def putChild(self, path, child):
        XMLPage.putChild(self, path, child)
        if path not in self.order:
            self.order.append(path)

    def xml(self):
        stat = etree.Element("Stat")

        for path in self.order:
            if not path:
                continue

            child = self.children[path]
            stat.append(child.xml())

        return stat

class NagcatStat(Stat):
    """Nagcat specific stat page"""

    def __init__(self, scheduler):
        Stat.__init__(self)

        self.putChild("scheduler", Scheduler(scheduler))

class MonitorSite(server.Site):
    """The whole monitoring api wrapped up in dark chocolate"""

    noisy = False

    def __init__(self, scheduler=None):
        if etree is None:
            raise errors.InitError("lxml is required for the monitoring api")

        if scheduler:
            stat = NagcatStat(scheduler)
        else:
            stat = Stat()

        self.root = resource.Resource()
        self.root.putChild("stat", stat)

        server.Site.__init__(self, self.root)
