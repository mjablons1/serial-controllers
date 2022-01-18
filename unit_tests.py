# -*- coding: utf-8 -*-
"""
Created on Tue Oct 12 10:22:10 2021

@author: MJABLONS
"""

import serial_controllers as sc

import unittest
from unittest import mock
from parameterized import parameterized


class TestDeviceModels(unittest.TestCase):

    def setUp(self):

        self.serial_dev_models = [sc.AgilentU12xxxDmm, sc.Tti2ChPsu, sc.Tti3ChPsu, sc.Fluke28xDmm,
                                  sc.RohdeHmp4ChPsu, sc.RohdeHmp2ChPsu]

        self.tcp_dev_models = [sc.GlOpticTouch]

        print('RUNNING SETUP:')
        self.dev_instances = []
        for n, dev_model in enumerate(self.serial_dev_models):
            self.dev_instances.append(dev_model(f'COM-{n}'))

    #@parameterized.expand([(serial_dev_model,) for serial_dev_model in serial_dev_models])
    #@mock.patch('serial_controllers.serial')
    def test_get_input_on_serial_dev_returns_tuple(self):

        with mock.patch('serial_controllers.serial') as mock_serial:

            for dev in self.dev_instances: # we could loop over a list of tuples of device class and their corresponding mock readily set up to mimic that specific device answers.
                with self.subTest():

                    # TODO it should be possible to call a generic method here that will allow mock to respond to read (
                    #  and optionally to write) with a fake message that follows the encoding and delimiting settings of
                    #  a given measurement device class just to have actual strings being passed forth and back in the
                    #  tests execution. It seems necessary on all models that attempt to modify the serial responses (
                    #  e.g. if they are mock object instead a string they can raise error e.g. when trying to iterate on
                    #  them.) We can use autospec and define return messages to the methods actually called by these
                    #  models. (serial.write() and serial.read_until())
                    dev.initialize() # consider adding optional interface named argument to initialize to be more explicit passing a mock there in testing
                    # then we dont really need to use the patching which is just avoidance of correcting the design flaw with initialize()

                    # mock_serial.configure_mock() # this would be more useful if reusable.. agin this part should go into setUp
                    return_mock_message = ('mock,answer' + dev.DEFAULTS['read_termination']).encode(dev.DEFAULTS['encoding'])

                    #mock_serial.read_until = mock.Mock(return_value=return_mock_message) # this does not work
                    dev._rsc.read_until = mock.Mock(return_value=return_mock_message) # this does work.. hmm

                    for channel in range(dev.MAX_CHANNELS):
                        ans = dev.get_input(channel)
                        if type(ans) is not tuple:
                            self.fail(f' \n{dev} \n returned {type(ans)} instead of a tuple on get_input({channel})')

if __name__ == '__main__':
    # in PyCharm you need to ALT+SHIFT+F10 to select standard runner so that unit test is executed instead of pytest.
    # Default runner is pytest and changing the runner setup does not seem to take any effect.

    unittest_return = unittest.main(exit=False)





