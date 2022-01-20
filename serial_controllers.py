from abc import ABC, abstractmethod
from time import sleep
import xml.etree.ElementTree as et
from datetime import datetime

import socket

try:
    import serial
except ImportError as e:
    serial = None
    exc1 = e


class BaseDevice(ABC):
    """Prototype class for a device"""
    # TODO : create some example keys for DEFAULTS dict for illustration
    DEFAULTS = dict()  # normally used to store communication settings matching to a specific device defaults
    MAX_CHANNELS = 1  # number of independent measurement channels or outputs present in the device. A
    # device with no selectable measurement channels/outputs is understood to be a 1 channel device.

    def __init__(self):
        """ Not much to do here beside eventual attribute assignment. Use initialize to establish the actual
        connection to the device so that no new instance is immediately creating that workload. """
        self._port = None  # identification of physical / virtual port at which the hardware is found / assigned.
        self._rsc = None  # resource object for pushing communications (e.g. serial or TCP socket).
        self._id = 'UNKNOWN DEVICE'  # identification of the meas. instrument (e.g. IDN string or network IP address.).

    def __str__(self):
        return f'\nDevice model: {self._id} at Port {self._port} \n Communication settings: {self.DEFAULTS}'

    @abstractmethod
    def initialize(self, interface=None):
        """ Establish communication / open port using instance or class attributes. """
        pass

    @abstractmethod
    def idn(self):
        """ Request the device to introduce itself to you. """
        pass

    @abstractmethod
    def beep(self):
        """ Request the device to make itself stand out from the physical test setup by making a sound, if possible.
        It's so cool when it does that. """
        pass

    @abstractmethod
    def get_input(self, channel: int) -> tuple[str, ...]:
        """ Get measurement input from a specific measurement channel. The response tuple should divide between
        measurement value string and unit information string. Method should construct a device-specific message and
        pass it to the device with _query. """
        pass

    @abstractmethod
    def set_output(self, channel: int, output_parameters):
        """ Set output parameters at a specific measurement channel. Method should construct a device-specific
        message and pass it to the device with _write (if device does not acknowledge) or _query (if device is
        expected to acknowledge). """
        pass

    def _query(self, message: str) -> str:
        """ Write a message and read the response in one method.
        Parameters
        ----------
        message : str
            message to send to the device
        Returns
        -------
            str whatever the output message
        """
        self._write(message)
        return self._read()

    @abstractmethod
    def _write(self, message: str):
        """ Lowest level write to whatever communication API represented by self._rsc. """
        pass

    @abstractmethod
    def _read(self) -> str:
        """ Lowest level read from whatever communication API represented by self._rsc. """
        pass

    def finalize(self):
        """
        Closes the resource
        Returns
        -------
            None
        """
        if self._rsc is not None:
            self._rsc.close()
            self._rsc = None
            print(f'({self._port}) Released resource:\n {self._id}')

    def channel_exists(self, channel: int) -> bool:
        """
        True if channel exits on this class
        Parameters
        ----------
        channel : int - channel number

        Returns
        -------

        """
        if 0 < channel <= self.MAX_CHANNELS:
            return True
        else:
            return False

    def _channel_nr_check(self, channels: int | tuple[int, ...]):
        """
        Checks that channel does not exceed the number of channels for this device.
        Parameters
        ----------
        channels:  number(s) of measurement / output channels

        Returns
        -------
        None

        """

        if not self.is_iterable(channels):
            channels = (channels,)

        for channel in channels:
            assert self.channel_exists(channel), f'This device does not support channel {channel}'

    @staticmethod
    def is_iterable(an_object):
        try:
            iter(an_object)
        except TypeError:
            return False
        return True


class SerialDevice(BaseDevice):

    """
    Controller class based on Python for the Lab course material of Aquiles Carattino.
    Parameters
    ----------
    port : str
        The port where the device is expected to be connected. Something like COM3 on Windows, or /dev/ttyACM0 on Linux
    Attributes
    ----------
    _rsc : serial
        The serial communication interface
    _port : str
        The port where the device is expected to be connected, such as COM3 or /dev/ttyACM0
    _id : str
        Identification string returned by the hardware
    """

    DEFAULTS = {'write_termination': '\n',
                'read_termination': '\n',
                'encoding': 'ascii',
                'baudrate': 9600,
                'read_timeout': 1,
                'write_timeout': 1,
                }

    MAX_CHANNELS = 2  # TODO not sure if there is any good reason to override here

    def __init__(self, port: str):

        # Remind user to install serial package to use any serial device:
        if serial is None:
            raise ImportError(f'{self.__class__.__name__} requires module "serial", which failed on import with '
                              f'error:\n{exc1}')

        super().__init__()
        self._port = port

    def initialize(self, interface=serial):
        """
        Opens the serial port with the DEFAULTS.
        The interface argument is meant to simplify unit testing with Mock so that no patching has to be done.
        """
        self._rsc = interface.Serial(port=self._port,
                                     baudrate=self.DEFAULTS['baudrate'],
                                     timeout=self.DEFAULTS['read_timeout'],
                                     write_timeout=self.DEFAULTS['write_timeout'])
        sleep(0.1)
        self._id = self.idn()

        if self._id == '':
            # pySerial returns empty string instead of raising read timeout exception for some reason when you
            # query the wrong resource using read_until(). See https://github.com/pyserial/pyserial/issues/108. This
            # workaround isn't perfect because, theoretically, if the resource replies with some error message it
            # will probably be taken for a valid ID.
            raise serial.SerialException(f'The resource did not identify itself correctly (Received id: {self._id}). '
                                         f'Its most likely that you have specified an existing, but incorrect COM '
                                         f'port for this device. Alternatively you are sending the wrong IDN request '
                                         f'message for this device type. In the later case please override the '
                                         f'inherited idn() method with one that uses the correct identification '
                                         f'request message.')

        print(f'({self._port}) Initialized resource:\n {self._id}')
        self.beep()

    def idn(self):
        """
        Get the serial number from the device.
        Returns
        -------
            str identification of the device
        """
        return self._query('*IDN?')

    def beep(self):
        """
        Request device to make a sound.
        Returns
        -------
            None
        """
        # TODO _query may be slowing down initialize due to timeout in case device does not respond back.
        self._query('SYST:BEEP')

    def get_input(self, channel: int) -> str:
        """
        Get current reading
        Parameters
        ----------
        channel :
            channel number

        Returns
        -------
            answer containing the reading
        """
        message = f'IN:CH{channel}'
        ans = self._query(message)
        
        return ans

    def set_output(self, channel: int, output_value: int):
        """
        Set analog output on a channel
        Parameters
        ----------
        channel :
            number of output channel
        output_value :
            output value in the range 0-4095
        Returns
        -------
            None
        """
        message = f'OUT:CH{channel}:{output_value}'
        self._query(message)  # reads any potential device response from the message buffer but ignores them.

    def _write(self, message: str):
        """
        Write message to the resource
        Parameters
        ----------
        message :
            message to be sent to the device

        Returns
        -------
            None

        """
        message = message + self.DEFAULTS['write_termination']
        message = message.encode(self.DEFAULTS['encoding'])
        self._rsc.write(message)

    def _read(self) -> str:
        """
        Read message from the resource
        Returns
        -------
            str message returned by device
        """
        # ans = self._rsc.readline() # readline() assumes \n as escape character causing read timeout on devices that
        # use any other read termination character.
        escape_char = bytes(self.DEFAULTS['read_termination'], self.DEFAULTS['encoding'])
        ans = self._rsc.read_until(escape_char)  # ... this is why read_until is used
        # print(f'##### Raw answer is: {ans}') #debug only
        ans = ans.decode(self.DEFAULTS['encoding']).strip()
        return ans

    # TODO this should be superfluous because base device implements this already, but for some reason,
    #  after removing _query from here, pyCharm checker complains that _query() 'does not return anything(?)'
    #  whenever Serial device child calls it.

    # def _query(self, message: str) -> str:
    #     """ Write a message and read the response in one method.
    #     Parameters
    #     ----------
    #     message :
    #         message to send to the device
    #     Returns
    #     -------
    #         Whatever the output message
    #     """
    #     self._write(message)
    #     return self._read()


class AgilentU12xxxDmm(SerialDevice):
    """
    Agilent U12xxx DMM basic controller
    """

    DEFAULTS = {'write_termination': '\r\n',
                'read_termination': '\r\n',
                'encoding': 'ascii',
                'baudrate': 9600,
                'read_timeout': 1,
                'write_timeout': 1,
                }

    MAX_CHANNELS = 2

    def get_input(self, channel: int) -> tuple[str, str]:
        """
        Get current reading
        Parameters
        ----------
        channel :
            1 - gets primary display reading
            2 - gets secondary display reading
        Returns
        -------
            tuple of strings with measurement reading and corresponding unit of measure
        """

        self._channel_nr_check(channel)

        reading_message = 'FETC?'
        unit_message = 'CONF?'

        if channel == 1:
            pass
        elif channel == 2:
            reading_message += ' @3'  # with some other DMM numbers it could be ' @2', you may have to experiment.
            unit_message += ' @3'

        reading = self._query(reading_message)
        unit = self._query(unit_message)

        # output format strongly depends on hw device exact model, more here:
        # https://sigrok.org/wiki/Agilent_U12xxx_series

        return reading, unit

    def set_output(self, channel, output_value):
        print(f'Device class {self.__class__.__name__} does not allow control of its output\n')


class RohdeHmp4ChPsu(SerialDevice):
    """
    Rohde & Shwarz HMP4000 basic controller
    """
    DEFAULTS = {'write_termination': '\n',
                'read_termination': '\n',
                'encoding': 'ascii',
                'baudrate': 9600,
                'read_timeout': 1,
                'write_timeout': 1,
                }

    MAX_CHANNELS = 4

    def initialize(self, *args, **kwargs):
        super().initialize(*args, **kwargs)
        self._disengage_all_outputs()

    def get_input(self, channel: int) -> tuple[str, str, str, str]:
        """
        Get voltage and current readings from a channel
        Parameters
        ----------
        channel :
            channel number
        Returns
        -------
            tuple of strings containing the channel reading and corresponding units of measure
        """
        self._channel_nr_check(channel)

        self._write(f'INST:NSEL {str(channel)}')
        voltage = self._query('MEAS:VOLT?')
        current = self._query('MEAS:CURR?')

        return voltage, 'Volt', current, 'Amp'

    def set_output(self, channel: int, voltage: float = 0.0, current: float = 0.0):
        """
        Set output voltage and current limits at a specific channel

        NOTE: be careful when changing voltage and current settings when outputs are engaged. There may also be a time
        delay between setting voltage and current limit that can cause transient state which could be dangerous
        for your DUT.

        Parameters
        ----------
        channel :
            channel number
        voltage : float
            channel voltage limit in volts
        current : float
            channel current limit in ampere
        Returns
        -------
            None
        """
        self._channel_nr_check(channel)

        self._write(f'INST:NSEL {str(channel)}')
        # set output levels
        self._write(f"VOLT {str(voltage)}{self.DEFAULTS['write_termination']}CURR {str(current)}")
        # NOTE: Second write termination is added by write. This is a workaround to ensure minimum time delay between
        # setting voltage and current but acc. to the device documentation the downside is that you cant be certain
        # as to the order of the two commands execution.

    def engage_output(self, channels: tuple[int, ...] | int, seek_permission: bool = True) -> int:
        """
        Engage outputs on specific channel(s) with or without user permission.
        Parameters
        ----------
        channels :
            channel or channels to be activated
        seek_permission :
            True - seek user permission before activating the outputs
            False - activate outputs without any permission (dangerous for your DUT!)
        Returns
        -------
            int 1 - output engage command sent
                0 - output engage command was not sent because user permission was not granted
        """

        self._channel_nr_check(channels)

        if type(channels) is int:
            channels = (channels,)  # place channel int into a tuple to keep code below DRY.

        self.disengage_output()
        self._activate_channels(channels)

        if seek_permission:
            print(f'\nDevice {self._id}:\n requesting permission to engage outputs->')
            for channel in channels:
                # select channel
                self._write(f'INST:NSEL {str(channel)}')
                # query input level settings to inform user prior to seeking permission.
                sel_voltage = self._query('VOLT?')
                sel_current = self._query('CURR?')
                print(f'  Ch:{channel} @: {sel_voltage} Volt / {sel_current} Amp')       
            
            usr_ans = input(f' Are you sure you want to proceed?[y/n] > ')
            if usr_ans.lower() != 'y':
                print('   Skipping outputs engage.\n')
                return 0
            
        self._write('OUTP:GEN 1')
        return 1

    # TODO: not sure if reaching for class attributes in default arguments is robust, i think I saw it backfire once.
    def _deactivate_channels(self, channels: tuple[int, ...] = tuple(range(1, MAX_CHANNELS+1))):
        """
        Deactivate all channels 'at once'.
        Parameters
        ----------
        channels -
            channel numbers to deactivate
        -------
        """

        long_msg = []
        for channel in channels:
            long_msg.append(f'INST:NSEL {str(channel)}{self.DEFAULTS["write_termination"]}OUTP:SEL 0'
                            f'{self.DEFAULTS["write_termination"]}')
            #  This is a workaround to get the selected channels to shut down as much together as possible (separate
            #  queries can take long and that can lead to in-between outputs state that user may not expect).
            #  SCPI standard allows to separate commands with semicolon (;) to send more commands in a single message
            #  but this device does not seem to support that.
        self._write("".join(long_msg))
    
    def _activate_channels(self, channels: tuple = tuple(range(1, MAX_CHANNELS+1))):
        """
        Activate all channels one by one.
        Parameters
        ----------
        channels - tuple
            numbers of channels
        Returns
        -------
        None
        """

        for channel in channels:
            # select channel
            self._write(f'INST:NSEL {str(channel)}')
            # activate channel
            self._write('OUTP:SEL 1')

    def disengage_output(self, channels: int | tuple[int, ...] | None = None):
        """
        Disengage outputs on specific channels at once.
        Parameters
        ----------
        channels : tuple of int
            number(s) of output channel(s) to disengage, when not passed all outputs will be disengaged
        Returns
        -------
            None
        """

        if channels is None or channels == tuple(range(1, self.MAX_CHANNELS+1)):
            self._disengage_all_outputs()
        else:
            self._channel_nr_check(channels)

            if type(channels) is int:
                channels = (channels,)  # make channels iterable to keep DRY.

            self._deactivate_channels(channels)

    def _disengage_all_outputs(self):
        """
        Shuts down all outputs at once and subsequently deactivates all channels.
        Returns
        -------
            None
        """
        self._write('OUTP:GEN 0')  # immediate shut down of all outputs
        self._deactivate_channels()  # activate / deactivate has to follow as we abstract this feature from user
        # completely and want to hide it from the interface to simplify use.


class RohdeHmp3ChPsu(RohdeHmp4ChPsu):
    """
    Rohde & Shwarz HMP2030 basic controller
    """
    MAX_CHANNELS = 3


class RohdeHmp2ChPsu(RohdeHmp4ChPsu):
    """
    Rohde & Shwarz HMP2020 basic controller
    """
    MAX_CHANNELS = 2


class Fluke28xDmm(SerialDevice):
    """
    Fluke 28x DMM basic controller
    """

    DEFAULTS = {'write_termination': '\r',
                'read_termination': '\r',
                'encoding': 'ascii',
                'baudrate': 115200,
                'read_timeout': 1,
                'write_timeout': 1,
                }

    MAX_CHANNELS = 1

    def idn(self) -> str:
        """
        Query device identification number.
        Returns
        -------
            str identification of the device
        """
        # First portion is just query confirmation (0 or 1). We want to read it out and disregard it hence _query call.
        self._query('ID')
        return self._read()  # Next part is the actual ID info

    def get_input(self, channel: int = 1) -> tuple[str, str]:
        """
        Get current primary display reading.
        Parameters
        ----------
        channel :
            1 - get primary display reading
                Currently only primary display reading is supported
        Returns
        -------
            tuple of strings with measurement reading and device specific representation of the unit
        """
        self._channel_nr_check(channel)
        self._query('QM')
        ans = self._read()
        print(f'ans: {ans}')
        reading, unit = tuple(item.strip() for item in ans.split(','))

        return reading, unit

    def set_output(self, channel, output_value):
        print(f'Device class {self.__class__.__name__} does not allow control of its output.\n')


class Tti3ChPsu(SerialDevice):
    """
    TTI 3 channel PSU basic controller
    """
    DEFAULTS = {'write_termination': '\n',
                'read_termination': '\r\n',
                'encoding': 'ascii',
                'baudrate': 9600,
                'read_timeout': 1,
                'write_timeout': 1,
                }

    MAX_CHANNELS = 3

    def initialize(self, *args, **kwargs):
        super().initialize(*args, **kwargs)
        self._disengage_all_outputs()

    def get_input(self, channel: int) -> tuple[str, str, str, str]:
        """
        Get voltage and current reading from a channel.
        Parameters
        ----------
        channel
            channel number
        Returns
        -------
            tuple of strings containing the measurement reading and corresponding unit of measure
        """

        self._channel_nr_check(channel)
        voltage = self._query(f'V{str(channel)}O?')[:-1]
        current = self._query(f'I{str(channel)}O?')[:-1]

        return voltage, 'Volt', current, 'Amp'

    def set_output(self, channel: int, voltage: float = 0.0, current: float = 0.0):
        """
        Set output voltage and current limits at specific channel

        NOTE: be careful when changing voltage and current settings when outputs are engaged. There may also be a time
        delay between setting voltage and current limit that can cause transient state which could be dangerous
        for your DUT.

        Parameters
        ----------
        channel :
            channel number(s)
        voltage :
            channel voltage limit in volts
        current :
            channel current limit in ampere
        Returns
        -------
            None
        """

        self._channel_nr_check(channel)
        self._write(f'V{str(channel)} {str(voltage)};I{str(channel)} {str(current)}')

    def engage_output(self, channels: tuple[int, ...] | int, seek_permission: bool = True) -> int:
        """
        Engage outputs on specific channels with user permission.
        Parameters
        ----------
        channels :
            output channel or channels to be engaged
        seek_permission :
            True - seek user permission before activating the outputs
            False - activate outputs without any permission (dangerous for your DUT!)
        Returns
        -------
            1 - output engage command sent,
            0 - output engage command was not sent because user permission wasn't granted
        """

        self._channel_nr_check(channels)
        self.disengage_output()

        if type(channels) is int:
            channels = (channels,)  # make channels iterable to keep DRY.

        if seek_permission:
            # TODO: below code is near identical for both PSU classes. Perhaps it would be worthwhile to unify by
            #  calling get_input instead of _query and def a dedicated SerialDevice method (i.e.
            #  _get_permission_to_engage()). Downside is that each device will return a little different string
            #  formatting for voltage and current.
            print(f'\nDevice {self._id}:\n requesting permission to engage outputs->')
            for channel in channels:
    
                # query input level settings to inform user prior to seeking permission.
                # The response is V <n> <nr2> where <nr2> is in Volts
                sel_voltage = self._query(f'V{str(channel)}?')[3:]
                sel_current = self._query(f'I{str(channel)}?')[3:]
                print(f'  Ch:{channel} @: {sel_voltage} Volt / {sel_current} Amp')

            usr_ans = input(f' Are you sure you want to proceed?[y/n] > ')
            if usr_ans.lower() != 'y':
                print('   Skipping outputs engage.\n')
                return 0
        
        # construct one message with request to engage each of the channels:
        long_msg = []
        for channel in channels:
            long_msg.append(f'OP{str(channel)} 1;')

        # For a specific group of channels to be engaged/disengaged its not possible to do so perfectly at the same
        # time - we inadvertently introduce an in-between state similar to error generation in imperfect binary
        # conversions. In order to reduce the amount of time the PSU spends going between current and required
        # outputs state the messages for each channel disengagement are bunched into one long communication which
        # should reduce the process time to the real-time capability of the PSU microcontroller on the receiving end
        # and that is normally orders of magnitude faster than making repeated _write() calls that suffer from
        # operating system delays and slow baud rate of each serial transmission.'

        self._write("".join(long_msg))
        return 1

    def disengage_output(self, channels: int | tuple[int, ...] | None = None):
        """
        Disengage outputs on specific channels at once.
        Parameters
        ----------
        channels :
            number(s) of output channel(s) to disengage, when not passed all 
            outputs will be disengaged by default.
        Returns
        -------
            None
        """

        if channels is None or channels == tuple(range(1, self.MAX_CHANNELS+1)):
            self._disengage_all_outputs()
        else:
            self._channel_nr_check(channels)

            if type(channels) is int:
                channels = (channels,)  # make channels iterable to keep DRY.

            long_msg = []
            for channel in channels:
                long_msg.append(f'OP{str(channel)} 0;')

            self._write(''.join(long_msg))

    def _disengage_all_outputs(self):
        """
        Shuts down all outputs at once.
        Returns
        -------
            None
        """
        self._write('OPALL 0')  # immediate shut down of all outputs


class Tti2ChPsu(Tti3ChPsu):
    """
    TTI 2 channel PSU basic controller
    """
    MAX_CHANNELS = 2


class Tti1ChPsu(Tti3ChPsu):
    """
    TTI 1 channel PSU basic controller
    """
    MAX_CHANNELS = 1


class TtiQL2ChPsu(Tti2ChPsu):
    """
    TTI QL564TP / QL355TP  2 channel PSU basic controller
    """
    DEFAULTS = {'write_termination': '\n',
                'read_termination': '\r\n',
                'encoding': 'ascii',
                'baudrate': 19200,  # QL series is fixed at higher baud rate by default
                'read_timeout': 1,
                'write_timeout': 1,
                }


class TtiQL1ChPsu(TtiQL2ChPsu):
    """
    TTI QL564P / QL355P 1 channel PSU basic controller
    """
    MAX_CHANNELS = 1


class GlOpticTouch(BaseDevice):

    DEFAULTS = {'write_prefix': '<',
                'write_termination': ' />',
                'encoding': 'UTF-8',  # UTF-8 is default for xml output but the files returned do not contain prolog
                "HOST": '127.0.0.1',
                "PORT": 12001,
                "read_buffer": 32768,
                "timeout": 20,  # this value has to be kept long since extremely dimm light sources can cause very
                # lengthy auto integration time and in these cases you have to wait long for the result (
                # experimentally up to about 15s)
                "meas_request": 'request name="measure" beep="on" mode="direct" integration_time="5000" '
                                'repeat_count="1" auto="on"'}  # with auto="on" integration_time is ignored.

    MAX_CHANNELS = 1

    # PORT: Same port that GL SPECTROSOFT establishes (use netstat in case its different in case of your equipment)

    def __init__(self):

        super().__init__()

        self.xml_dump_file_name = None  # if overwritten with str file dumping with that str in file name as prefix
        # will be dumped for every measurement. If user specifies any other type it will be ignored.
        # TODO: implement as _xml... and set up decorated setter and getter with @property and
        #  @xml_dump_file_name.setter, although at this point it appears as unnecessary boilerplate...

    def initialize(self, interface=socket):

        # set up TCP client to talk to the Spectrosoft local host at port 12001
        spectrosoft_client_socket = interface.socket(interface.AF_INET, interface.SOCK_STREAM)
        spectrosoft_client_socket.settimeout(self.DEFAULTS['timeout'])
        
        try:
            spectrosoft_client_socket.connect((self.DEFAULTS['HOST'], self.DEFAULTS['PORT']))
        except ConnectionRefusedError:
            raise ConnectionRefusedError('Could not connect to SpectroSoft. Please verify that SpectroSoft software '
                                         'is runnning in the background.\n(NOTE: you need a hardware USB key to run '
                                         'SpectroSoft)')

        host, port = spectrosoft_client_socket.getpeername()
        
        print(f'Connected to SpectroSoft host ({host}) at port {port}.')

        self._id = host
        self._port = port
        self._rsc = spectrosoft_client_socket

    def idn(self):
        return self.__str__()

    def beep(self):
        raise NotImplementedError(f'This device can only beep when making a measurement. If you really need it to '
                                  f'make a sound you could trigger a dummy, short integration time measurement from '
                                  f'within beep method.')

    def _write(self, message: str):
        message = self.DEFAULTS['write_prefix'] + message + self.DEFAULTS['write_termination']
        message = message.encode(self.DEFAULTS['encoding'])
        self._rsc.sendall(message)

    def _read(self):
        # data returned by recv is readily xml format bytes type
        try:  # we could decode here DEFAULTS[encoding] but et.fromstring can manage bytes type as well as str.
            gl_xml_bytes = self._rsc.recv(self.DEFAULTS['read_buffer'])
        except socket.timeout as err_msg:
            print(err_msg)
            # pyCharm inspection throws  expected int arg on class that inherits from builtin TimeoutError ...?
            raise socket.timeout('Could not obtain measurement data from spectrometer.\n Please check the USB '
                                       'connection between PC and the Spectrometer.')
        
        return self._parse_xml_to_dict(gl_xml_bytes, xml_dump=self.xml_dump_file_name)

    def get_input(self, *args):
        """ Trigger and return measurement output in form of results dictionary

        Parameters
        ----------
        *args :
            int channel - optional channel argument (now unused)

        Returns
        -------

        """
        return self._query(self.DEFAULTS['meas_request'])

    def set_output(self, *args):
        """ Not implemented.

        Parameters
        ----------
        args :
            tuple (int channel, any output_parameters) optional parameters (now unused)

        Returns
        -------

        """
        # TODO The measurement message could be modified by this interface without any actual communications here.
        raise NotImplementedError(f'This is not implemented. If you wish to change the measurement parameters you can '
                                  f'modify the DEFAULTS[meas_request] string attribute values. Currently '
                                  f'these attributes are set to {self.DEFAULTS["meas_request"]}')

    @staticmethod
    def _parse_xml_to_dict(xml_string: str | bytes, xml_dump: bool | str = False) -> dict:
        root = et.fromstring(xml_string)

        if xml_dump is True:
            xml_dump = ''

        if type(xml_dump) is str:
            date_str = datetime.now().strftime("%Y_%m_%d_%H%M%S")
            file_name = xml_dump.strip('.xml') + date_str + '.xml'
            et.ElementTree(root).write(file_name)

        ans_dict = dict(results=dict(), status=dict(), data=dict(spectrum_x=[], spectrum_y=[]))

        # flatten the data structure to name attributes only (caption atrributes are not very readable and contain
        # unusual complex characters)
        for parameter in root.find('status'):
            ans_dict['status'][parameter.attrib.get('name')] = parameter.text  # TODO unexpected type linter complaint

        # collect tagged data
        data = root.find('data')
        for parameter in data:
            # Avoid creating 'row' key entry as that would contain only the first found row (and there are many)...
            if parameter.tag != 'row':
                ans_dict['data'][parameter.tag] = parameter.attrib

        for row in data.findall('row'):  # ...instead append all row elements into lists.
            ans_dict['data']['spectrum_x'].append(row.attrib.get('wavelength'))
            ans_dict['data']['spectrum_y'].append(row.attrib.get('value'))

        for parameter in root.find('results'):
            ans_dict['results'][parameter.attrib.get('name')] = parameter.text

        # TODO some of the items under 'results' have non obvious name attribute. Perhaps their content can be copied
        #  to additional entries with more friendly names (e.g. results_dict["Y"] = results_dict["luminous_flux"]),
        #  also one level deeper some static definitions of units can be added i.e.: results_dict["luminous_flux"][
        #  'unit'] since these are terribly missing in the xml returned by the device.

        return ans_dict


if __name__ == '__main__':
    pass
