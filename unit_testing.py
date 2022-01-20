# -*- coding: utf-8 -*-
"""
Created on Tue Oct 12 10:22:10 2021

@author: MJABLONS
"""

import serial
import serial_controllers as sc

import unittest
from unittest.mock import Mock, call


class TestAgilentU12xxxDmm(unittest.TestCase):

    def setUp(self):

        self.dev = sc.AgilentU12xxxDmm(f'COM-1')
        self.dev.initialize(interface=Mock(name='Serial Mock', spec=serial))

    def test_get_input1_message(self):

        channel = 1
        expected_msg1 = 'FETC?\r\n'.encode('ascii')
        expected_msg2 = 'CONF?\r\n'.encode('ascii')

        self.dev.get_input(channel)
        self.dev._rsc.write.assert_has_calls([call(expected_msg1), call(expected_msg2)])

    def test_get_input2_message(self):

        channel = 2
        expected_msg1 = 'FETC? @3\r\n'.encode('ascii')
        expected_msg2 = 'CONF? @3\r\n'.encode('ascii')

        self.dev.get_input(channel)
        self.dev._rsc.write.assert_has_calls([call(expected_msg1), call(expected_msg2)])

if __name__ == '__main__':
    # in PyCharm you need to ALT+SHIFT+F10 to select standard runner so that unit test is executed instead of pytest.
    # Default runner is pytest and changing the runner setup does not seem to take any effect.
    unittest.main()
    #unittest_return = unittest.main(exit=False)





