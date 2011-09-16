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

import re
import time

from twisted.internet import defer, reactor
from twisted.python import failure
from coil import struct

from nagcat import errors, filters, log, query, runnable, util, test

class MerlinTest(test.Test):

    def __init__(self,nagcat, conf, test_index):
        test.Test.__init__(self, nagcat, conf)

        self._nagcat = nagcat
        self._test_index = test_index

    def _should_run(self):
        """Decides whether or not a test should be run, based on its task
        index and the schedulers peer_id. Returns True if it should run, False
        if it should not."""
        peer_id = self._nagcat.get_peer_id()
        num_peers = self._nagcat.get_num_peers()
        log.debug("Running _should_run, test_index=%s, num_peers=%s, peer_id=%s", str(self._test_index), num_peers, peer_id)
        if peer_id and num_peers:
            if not (self._test_index % num_peers == peer_id):
                return False
        return True

    def start(self):
        """Decides whether or not to start the test, based on _should_run."""
        log.debug("Running MerlinTest.start")
        if self._should_run():
            log.debug("Running test %s", self)
            return super(MerlinTest,self).start()
        else:
            log.debug("Skipping start of %s", self)
            return defer.succeed(None)
