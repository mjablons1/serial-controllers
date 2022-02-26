# -*- coding: utf-8 -*-
"""
Created on Tue Oct 12 10:22:10 2021

@author: MJABLONS
"""

import serial_controllers as sc

import unittest
from unittest.mock import Mock, call, patch
from parameterized import parameterized

import sys
import os


class Silence:
    def __init__(self):
        self.old_stdout = sys.stdout

    def __enter__(self):
        # suppress printing to console
        sys.stdout = open(os.devnull, "w")
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        sys.stdout.close()
        # allow printing to console again
        sys.stdout = self.old_stdout


def arg_set_from_call_list(call_args_list: list[call]) -> set:
    """
    Utility function to nimble out a set of positional arguments with which calls were made.
    This utility function supports checking if a specific, unwanted message was called.
    This allows functionality similar to "assert_has_no_calls" that is missing in unittest library.
    Parameters
    ----------
    call_args_list
        list of calls that were made to a mocked interface.

    Returns -------
        set of first positional arguments with which calls were made.
    """
    write_msgs = set([])
    for call_to_write in call_args_list:
        args, kwargs = call_to_write
        write_msg, *_ = args
        write_msgs.add(write_msg)
    return write_msgs


class TestAgilentU12xxxDmm(unittest.TestCase):

    def setUp(self):
        self.dev = sc.AgilentU12xxxDmm(f'COM-1')
        serial_mock = Mock(name='Serial_Mock')
        with Silence():
            self.dev.initialize(interface=serial_mock)
            self.dev._rsc.read_until = Mock(return_value='mock_ans\r\n'.encode('ascii'))

    def test_get_input_wrong_channel_raises_exception(self, channel=42):
        with self.assertRaises(AssertionError):
            self.dev.get_input(channel)

    def test_get_input1_message(self, channel=1):
        expected_msg1 = 'FETC?\r\n'.encode('ascii')
        expected_msg2 = 'CONF?\r\n'.encode('ascii')

        self.dev.get_input(channel)
        self.dev._rsc.write.assert_has_calls([call(expected_msg1), call(expected_msg2)])

    def test_get_input2_message(self, channel=2):
        expected_msg1 = 'FETC? @3\r\n'.encode('ascii')
        expected_msg2 = 'CONF? @3\r\n'.encode('ascii')

        self.dev.get_input(channel)
        self.dev._rsc.write.assert_has_calls([call(expected_msg1), call(expected_msg2)])

    def test_get_input_returns_tuple_of_str(self, channel=1):
        expected_ans = ('mock_ans', 'mock_ans')

        ans = self.dev.get_input(channel)
        self.assertEqual(expected_ans, ans)


class TestFluke28xDmm(unittest.TestCase):

    def setUp(self):
        self.dev = sc.Fluke28xDmm(f'COM-1')
        serial_mock = Mock(name='Serial_Mock')
        with Silence():
            self.dev.initialize(interface=serial_mock)
            self.dev._rsc.read_until = Mock(return_value='mock_ans_, mock_ans_, mock_ans_, mock_ans_\r'.encode('ascii'))

    def test_get_input_wrong_channel_raises_exception(self, channel=42):
        with self.assertRaises(AssertionError):
            self.dev.get_input(channel)

    def test_get_input1_message(self, channel=1):
        expected_msg = 'QM\r'.encode('ascii')

        self.dev.get_input(channel)
        self.dev._rsc.write.assert_has_calls([call(expected_msg)])

    def test_get_input_returns_tuple_of_str(self, channel=1):
        expected_ans = ('mock_ans', 'mock_ans')

        ans = self.dev.get_input(channel)
        self.assertEqual(expected_ans, ans)


class TestRohdeHmp4ChPsu(unittest.TestCase):

    def setUp(self):
        self.dev = sc.RohdeHmp4ChPsu(f'COM-1')
        serial_mock = Mock(name='Serial_Mock')
        with Silence():
            self.dev.initialize(interface=serial_mock)
            self.dev._rsc.read_until = Mock(return_value='mock_ans\r\n'.encode('ascii'))

    def test_get_input_wrong_channel_raises_exception(self, channel=42):
        with self.assertRaises(AssertionError):
            self.dev.get_input(channel)

    @parameterized.expand([(1,), (2,), (3,), (4,)])
    def test_get_input_message(self, channel):
        expected_msg1 = f'INST:NSEL {channel}\n'.encode('ascii')
        expected_msg2 = 'MEAS:VOLT?\n'.encode('ascii')
        expected_msg3 = 'MEAS:CURR?\n'.encode('ascii')

        self.dev.get_input(channel)
        self.dev._rsc.write.assert_has_calls([call(expected_msg1), call(expected_msg2), call(expected_msg3)])

    def test_get_input_returns_tuple_of_str(self, channel=1):
        expected_ans = ('mock_ans', 'Volt', 'mock_ans', 'Amp')

        ans = self.dev.get_input(channel)
        self.assertEqual(expected_ans, ans)

    @parameterized.expand([(1,), (2,), (3,), (4,)])
    def test_set_output_sets_zeros_by_default(self, channel):
        expected_msg1 = f'INST:NSEL {channel}\n'.encode('ascii')
        expected_msg2 = f'VOLT 0.0\nCURR 0.0\n'.encode('ascii')

        self.dev.set_output(channel)
        self.dev._rsc.write.assert_has_calls([call(expected_msg1), call(expected_msg2)])

    @parameterized.expand([(1,), (2,), (3,), (4,)])
    def test_set_output_message(self, channel):
        expected_msg1 = f'INST:NSEL {channel}\n'.encode('ascii')
        expected_msg2 = f'VOLT 3.141592\nCURR 3.141592\n'.encode('ascii')

        self.dev.set_output(channel, voltage=3.141592, current=3.141592)
        self.dev._rsc.write.assert_has_calls([call(expected_msg1), call(expected_msg2)])

    def test_engage_output_with_permission_wrong_channel_raises_exception(self, channel=42):
        with unittest.mock.patch('builtins.input', return_value='y'):
            with Silence():
                with self.assertRaises(AssertionError):
                    self.dev.engage_output(channel)

    def test_engage_output_without_permission_wrong_channel_raises_exception(self, channel=42):
        with Silence():
            with self.assertRaises(AssertionError):
                self.dev.engage_output(channel, seek_permission=False)

    @parameterized.expand([(1,), (2,), (3,), (4,)])
    def test_engage_output_no_permission_returns_zero(self, channel):
        with unittest.mock.patch('builtins.input', return_value='n'):
            with Silence():
                ans = self.dev.engage_output(channel)
        self.assertEqual(ans, 0)

    @parameterized.expand([(1,), (2,), (3,), (4,)])
    def test_engage_output_w_permission_returns_one(self, channel):
        with unittest.mock.patch('builtins.input', return_value='y'):
            with Silence():
                ans = self.dev.engage_output(channel)
        self.assertEqual(ans, 1)

    @parameterized.expand([(1,), (2,), (3,), (4,)])
    def test_engage_output_no_permission_does_not_engage_output(self, channel):

        forbidden_msgs = set([f'OUTP:GEN 1\n'.encode('ascii')])

        # any other input than 'y' or 'Y' should be treated as no permission
        with unittest.mock.patch('builtins.input', return_value='x'):
            with Silence():
                ans = self.dev.engage_output(channel)

        # test if sequence will not lead to engaging of any of the output channels:
        with self.subTest('test_engage_output_no_permission_does_not_engage_output:B'):
            write_msgs = arg_set_from_call_list(self.dev._rsc.write.call_args_list)
            forbidden_write_msgs = write_msgs & forbidden_msgs

            if forbidden_write_msgs:
                self.fail(f'Unintended PSU output channel would have been engaged with messages:'
                          f'\n {forbidden_write_msgs})')

    @parameterized.expand([(1,), (2,), (3,), (4,)])
    def test_engage_output_message_with_permission(self, channel):

        # select and activate a channel:
        expected_msg0 = f'INST:NSEL {channel}\n'.encode('ascii')  # select channel for checking
        expected_msg1 = f'OUTP:SEL 1\n'.encode('ascii')

        # select and check a channel output setting:
        expected_msg2 = f'INST:NSEL {channel}\n'.encode('ascii')  # select channel for checking
        expected_msg3 = f'VOLT?\n'.encode('ascii')  # check voltage setting level
        expected_msg4 = f'CURR?\n'.encode('ascii')  # check current setting level

        # engage the output:
        expected_msg5 = f'OUTP:GEN 1\n'.encode('ascii')

        unintended_channels = set(range(1, 5)) - set([channel])

        forbidden_msgs = set([f'INST:NSEL {unintended_channel}\n'.encode('ascii')
                              for unintended_channel in unintended_channels])

        with unittest.mock.patch('builtins.input', return_value='y'):  # mock permission
            with Silence():
                self.dev.engage_output(channel)

        # test if sequence will indeed lead to engaging of the intended output channel:
        with self.subTest('test_engage_output_message_with_permission:A'):
            self.dev._rsc.write.assert_has_calls([call(expected_msg0),
                                                  call(expected_msg1),
                                                  call(expected_msg2),
                                                  call(expected_msg3),
                                                  call(expected_msg4),
                                                  call(expected_msg5)])

        # test if sequence will not lead to engaging of any of the remaining, unintended output channels:
        with self.subTest('test_engage_output_message_with_permission:B'):
            write_msgs = arg_set_from_call_list(self.dev._rsc.write.call_args_list)
            forbidden_write_msgs = write_msgs & forbidden_msgs

            if forbidden_write_msgs:
                self.fail(f'Unintended PSU output channel would have been engaged with messages:'
                          f'\n {forbidden_write_msgs})')

    @parameterized.expand([(1,), (2,), (3,), (4,)])
    def test_engage_output_message_without_permission(self, channel):

        # select and activate a channel:
        expected_msg0 = f'INST:NSEL {channel}\n'.encode('ascii')  # select channel for checking
        expected_msg1 = f'OUTP:SEL 1\n'.encode('ascii')

        # engage the output:
        expected_msg2 = f'OUTP:GEN 1\n'.encode('ascii')

        unintended_channels = set(range(1, 5)) - set([channel])
        forbidden_msgs = set([f'INST:NSEL {unintended_channel}\n'.encode('ascii')
                              for unintended_channel in unintended_channels])

        with Silence():
            self.dev.engage_output(channel, seek_permission=False)

        # test if sequence will indeed lead to engaging of the intended output channel:
        with self.subTest('test_engage_output_message_without_permission:A'):
            self.dev._rsc.write.assert_has_calls([call(expected_msg0),
                                                  call(expected_msg1),
                                                  call(expected_msg2)])

        # test if sequence will not lead to engaging of any of the remaining, unintended output channels:
        with self.subTest('test_engage_output_message_without_permission:B'):
            write_msgs = arg_set_from_call_list(self.dev._rsc.write.call_args_list)
            forbidden_write_msgs = write_msgs & forbidden_msgs

            if forbidden_write_msgs:
                self.fail(f'Unintended PSU output channel would have been engaged with messages:'
                          f'\n {forbidden_write_msgs})')

    def test_disengage_output_message_defaults_to_all_outputs_disengage(self):

        expected_msg = f'OUTP:GEN 0\n'.encode('ascii')
        self.dev.disengage_output()
        self.dev._rsc.write.assert_has_calls([call(expected_msg)])

    @parameterized.expand([(1,), (2,), (3,), (4,)])
    def test_disengage_output_message(self, channel):

        # select and deactivate a channel (this automatically disengages the output):
        expected_msg = f'INST:NSEL {channel}\nOUTP:SEL 0\n'.encode('ascii')

        unintended_channels = set(range(1, 5)) - set([channel])
        forbidden_msgs = set([f'INST:NSEL {unintended_channel}\nOUTP:SEL 0\n'.encode('ascii')
                              for unintended_channel in unintended_channels])

        with Silence():
            self.dev.disengage_output(channel)

        # test if sequence will indeed lead to disengaging of the intended output channel:
        with self.subTest('test_disengage_output_message_without_permission:A'):
            self.dev._rsc.write.assert_has_calls([call(expected_msg)])

        # test if sequence will not lead to engaging of any of the remaining, unintended output channels:
        with self.subTest('test_disengage_output_message_without_permission:B'):
            write_msgs = arg_set_from_call_list(self.dev._rsc.write.call_args_list)
            forbidden_write_msgs = write_msgs & forbidden_msgs

            if forbidden_write_msgs:
                self.fail(f'Unintended PSU output channel would have been engaged with messages:'
                          f'\n {forbidden_write_msgs})')


class TestTti3ChPsu(unittest.TestCase):

    def setUp(self):
        self.dev = sc.Tti3ChPsu(f'COM-1')
        serial_mock = Mock(name='Serial_Mock')
        with Silence():
            self.dev.initialize(interface=serial_mock)
            self.dev._rsc.read_until = Mock(return_value='mock_ans\r\n'.encode('ascii'))

    def test_get_input_wrong_channel_raises_exception(self, channel=42):
        with self.assertRaises(AssertionError):
            self.dev.get_input(channel)

    @parameterized.expand([(1,), (2,), (3,)])
    def test_get_input_message(self, channel):
        expected_msg1 = f'V{channel}O?\n'.encode('ascii')
        expected_msg2 = f'I{channel}O?\n'.encode('ascii')

        self.dev.get_input(channel)
        self.dev._rsc.write.assert_has_calls([call(expected_msg1), call(expected_msg2)])

    def test_get_input_returns_tuple_of_str(self, channel=1):
        expected_ans = ('mock_ans', 'Volt', 'mock_ans', 'Amp')

        ans = self.dev.get_input(channel)
        self.assertEqual(expected_ans, ans)

    # TODO CONTINUE UPDATING MESSAGES FROM HERE:
    @parameterized.expand([(1,), (2,), (3,)])
    def test_set_output_sets_zeros_by_default(self, channel):
        expected_msg = f'V{channel} 0.0;I{channel} 0.0\n'.encode('ascii')

        self.dev.set_output(channel)
        self.dev._rsc.write.assert_has_calls([call(expected_msg)])

    @parameterized.expand([(1,), (2,), (3,)])
    def test_set_output_message(self, channel):
        expected_msg = f'V{channel} 3.141592;I{channel} 3.141592\n'.encode('ascii')

        self.dev.set_output(channel, voltage=3.141592, current=3.141592)
        self.dev._rsc.write.assert_has_calls([call(expected_msg)])

    def test_engage_output_with_permission_wrong_channel_raises_exception(self, channel=42):
        with unittest.mock.patch('builtins.input', return_value='y'):
            with Silence():
                with self.assertRaises(AssertionError):
                    self.dev.engage_output(channel)

    def test_engage_output_without_permission_wrong_channel_raises_exception(self, channel=42):
        with Silence():
            with self.assertRaises(AssertionError):
                self.dev.engage_output(channel, seek_permission=False)

    @parameterized.expand([(1,), (2,), (3,)])
    def test_engage_output_no_permission_returns_zero(self, channel):
        with unittest.mock.patch('builtins.input', return_value='n'):
            with Silence():
                ans = self.dev.engage_output(channel)
        self.assertEqual(ans, 0)

    @parameterized.expand([(1,), (2,), (3,)])
    def test_engage_output_w_permission_returns_one(self, channel):
        with unittest.mock.patch('builtins.input', return_value='y'):
            with Silence():
                ans = self.dev.engage_output(channel)
        self.assertEqual(ans, 1)

    @parameterized.expand([(1,), (2,), (3,)])
    def test_engage_output_no_permission_does_not_engage_output(self, channel):
        forbidden_msgs = set([f'OP{channel} 1\n'.encode('ascii'), f'OP{channel} 1;\n'.encode('ascii')])

        # any other input than 'y' or 'Y' should be treated as no permission
        with unittest.mock.patch('builtins.input', return_value='x'):
            with Silence():
                self.dev.engage_output(channel)

        # test if sequence will not lead to engaging of any of the output channels:
        with self.subTest('test_engage_output_no_permission_does_not_engage_output:B'):
            write_msgs = arg_set_from_call_list(self.dev._rsc.write.call_args_list)
            forbidden_write_msgs = write_msgs & forbidden_msgs

            if forbidden_write_msgs:
                self.fail(f'Unintended PSU output channel would have been engaged with messages:'
                          f'\n {forbidden_write_msgs})')

    @parameterized.expand([(1,), (2,), (3,)])
    def test_engage_output_message_with_permission(self, channel):

        # select channel output setting:
        expected_msg0 = f'V{channel}?\n'.encode('ascii')  # select channel for checking
        expected_msg1 = f'I{channel}?\n'.encode('ascii')  # check current setting level

        # engage the output:
        expected_msg2 = f'OP{channel} 1;\n'.encode('ascii')

        unintended_channels = set(range(1, 4)) - set([channel])
        forbidden_msgs = set([f'OP{unintended_channel} 1;\n'.encode('ascii')
                              for unintended_channel in unintended_channels])

        with unittest.mock.patch('builtins.input', return_value='y'):  # mock permission
            with Silence():
                self.dev.engage_output(channel)

        # test if sequence will indeed lead to engaging of the intended output channel:
        with self.subTest('test_engage_output_message_with_permission:A'):
            self.dev._rsc.write.assert_has_calls([call(expected_msg0),
                                                  call(expected_msg1),
                                                  call(expected_msg2)])

        # test if sequence will not lead to engaging of any of the remaining, unintended output channels:
        with self.subTest('test_engage_output_message_with_permission:B'):
            write_msgs = arg_set_from_call_list(self.dev._rsc.write.call_args_list)
            forbidden_write_msgs = write_msgs & forbidden_msgs

            if forbidden_write_msgs:
                self.fail(f'Unintended PSU output channel would have been engaged with messages:'
                          f'\n {forbidden_write_msgs})')

    @parameterized.expand([(1,), (2,), (3,)])
    def test_engage_output_message_without_permission(self, channel):

        # engage the output:
        expected_msg = f'OP{channel} 1;\n'.encode('ascii')

        unintended_channels = set(range(1, 4)) - set([channel])
        forbidden_msgs = set([f'OP{unintended_channel} 1;\n'.encode('ascii')
                              for unintended_channel in unintended_channels])

        with Silence():
            self.dev.engage_output(channel, seek_permission=False)

        # test if sequence will indeed lead to engaging of the intended output channel:
        with self.subTest('test_engage_output_message_without_permission:A'):
            self.dev._rsc.write.assert_has_calls([call(expected_msg)])

        # test if sequence will not lead to engaging of any of the remaining, unintended output channels:
        with self.subTest('test_engage_output_message_without_permission:B'):
            write_msgs = arg_set_from_call_list(self.dev._rsc.write.call_args_list)
            forbidden_write_msgs = write_msgs & forbidden_msgs

            if forbidden_write_msgs:
                self.fail(f'Unintended PSU output channel would have been engaged with messages:'
                          f'\n {forbidden_write_msgs})')

    def test_disengage_output_message_defaults_to_all_outputs_disengage(self):

        # disengage the output: below msg may look equivalent but its not exactly the optimal solution as its not
        # going to be executed perfectly synchronously on all channels. In view that there exists a method for
        # switching all channels at once its expected to be the only proper way to disengage all outputs.
        # expected_msg = "".join([f'OP{channel} 1;\n' for channel in range(1, 4)]).encode('ascii')
        expected_msg = f'OPALL 0\n'.encode('ascii')
        self.dev.disengage_output()
        self.dev._rsc.write.assert_has_calls([call(expected_msg)])

    @parameterized.expand([(1,), (2,), (3,)])
    def test_disengage_output_message(self, channel):

        # select and deactivate a channel (this automatically disengages the output):
        expected_msg = f'OP{channel} 0;\n'.encode('ascii')

        unintended_channels = set(range(1, 4)) - set([channel])
        # TODO another implementation may not write ";" but it does not mean its wrong.
        forbidden_msgs = set([f'OP{unintended_channel} 0;\n'.encode('ascii')
                              for unintended_channel in unintended_channels])

        with Silence():
            self.dev.disengage_output(channel)

        # test if sequence will indeed lead to disengaging of the intended output channel:
        with self.subTest('test_disengage_output_message_without_permission:A'):
            self.dev._rsc.write.assert_has_calls([call(expected_msg)])

        # test if sequence will not lead to engaging of any of the remaining, unintended output channels:
        with self.subTest('test_disengage_output_message_without_permission:B'):
            write_msgs = arg_set_from_call_list(self.dev._rsc.write.call_args_list)
            forbidden_write_msgs = write_msgs & forbidden_msgs

            if forbidden_write_msgs:
                self.fail(f'Unintended PSU output channel would have been engaged with messages:'
                          f'\n {forbidden_write_msgs})')


if __name__ == '__main__':
    # in PyCharm ALT+SHIFT+F10 to select unittest runner instead of the default, pytest runner.

    unittest.main()
    #unittest_return = unittest.main(exit=False)





