#!/usr/bin/env python

"""
@package ion.agents.platform.oms.test.test_oms_platform_driver
@file    ion/agents/platform/oms/test/test_oms_platform_driver.py
@author  Carlos Rueda
@brief   Basic OmsPlatformDriver tests
"""

__author__ = 'Carlos Rueda'
__license__ = 'Apache 2.0'


from pyon.public import log
import logging

from pyon.util.containers import get_ion_ts

from ion.agents.platform.oms.oms_client_factory import OmsClientFactory
from ion.agents.platform.oms.oms_util import RsnOmsUtil
from ion.agents.platform.util.network_util import NetworkUtil

from ion.agents.platform.oms.oms_platform_driver import OmsPlatformDriver

from pyon.util.int_test import IonIntegrationTestCase

from nose.plugins.attrib import attr

from gevent import sleep

from ion.agents.platform.test.helper import HelperTestMixin


DVR_CONFIG = {
    'oms_uri': 'embsimulator',
}


@attr('INT', group='sa')
class TestOmsPlatformDriver(IonIntegrationTestCase, HelperTestMixin):

    @classmethod
    def setUpClass(cls):
        HelperTestMixin.setUpClass()

    def setUp(self):

        # Use the network definition provided by RSN OMS directly.
        rsn_oms = OmsClientFactory.create_instance(DVR_CONFIG['oms_uri'])
        network_definition = RsnOmsUtil.build_network_definition(rsn_oms)

        if log.isEnabledFor(logging.DEBUG):
            network_definition_ser = NetworkUtil.serialize_network_definition(network_definition)
            log.debug("NetworkDefinition serialization:\n%s", network_definition_ser)

        platform_id = self.PLATFORM_ID
        self._plat_driver = OmsPlatformDriver(platform_id, DVR_CONFIG)

        self._plat_driver.set_nnode(network_definition.nodes[platform_id])

        self._plat_driver.set_event_listener(self.evt_recv)

    def evt_recv(self, driver_event):
        log.debug('GOT driver_event=%s', str(driver_event))

    def tearDown(self):
        self._plat_driver.destroy()

    def _ping(self):
        result = self._plat_driver.ping()
        self.assertEquals("PONG", result)

    def _go_active(self):
        self._plat_driver.go_active()

    def _get_attribute_values(self):
        attrNames = self.ATTR_NAMES

        # see OOIION-631 note in test_platform_agent_with_oms
        from_time = str(int(get_ion_ts()) - 50000)  # a 50-sec time window

        attr_values = self._plat_driver.get_attribute_values(attrNames, from_time)
        log.info("attr_values = %s" % str(attr_values))
        self.assertIsInstance(attr_values, dict)
        for attr_name in attrNames:
            self.assertTrue(attr_name in attr_values)

    def _start_event_dispatch(self):
        params = {}  # TODO params not used yet
        self._plat_driver.start_event_dispatch(params)

    def _stop_event_dispatch(self):
        self._plat_driver.stop_event_dispatch()

    def test(self):

        self._ping()
        self._go_active()

        self._get_attribute_values()

        self._start_event_dispatch()

        log.info("sleeping to eventually see some events...")
        sleep(15)

        self._stop_event_dispatch()
