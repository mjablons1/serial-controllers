import serial
from time import sleep
import xml.etree.ElementTree as et
from datetime import datetime

# Ensure module is usable even if user environment does not contain socket package.
try:
    import socket
except ImportError as exc1:
    socket = None


class BaseDevice: # TODO Turn this into base class with ABC?
    """Prototype class for a device"""
    def __init__(self):
        """ Not much to do here beside eventual attribute assignment. Use initialize to establish the actual
        connection to the device so that no new instance is immediately creating that workload. """
        self.port = None  # identification of physical / virtual port at which the hardware is found / assigned.
        self.rsc = None  # resource object for pushing communications (e.g. serial or TCP socket).
        self.id = 'UNKNOWN DEVICE'  # identification of the meas. instrument (e.g. IDN string or network IP address.).

    def initialize(self):
        """ Establish communication / open port using instance or class attributes."""
        pass

    def idn(self):
        """ Request the device to introduce itself to you. """
        pass

    def beep(self):
        """ Request the device to make itself stand out from the physical test setup by making a sound, if possible. """
        pass

    def get_input(self, channel):
        """ Get measurement input from a specific measurement channel.
         Method should construct a device-specific message and pass it to the device with _query."""
        pass

    def set_output(self, channel, output_parameters):
        """ Set output parameters at a specific measurement channel. Method should construct a device-specific
        message and pass it to the device with _write (if device does not acknowledge) or _query (if device is
        expected to acknowledge). """
        pass

    def _query(self, message):
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

    def _write(self, message):
        """ Lowest level write to whatever communication API represented by self.rsc. """
        pass

    def _read(self):
        """ Lowest level read from whatever communication API represented by self.rsc. """
        pass

    def finalize(self):
        """ Tear down whatever hardware communication established in the initialize method."""
        pass


class SerialDevice(BaseDevice):

    """
    Controller class based on Python for the Lab course material of Aquiles Carattino.
    Parameters
    ----------
    port : str
        The port where the device is connected. Something like COM3 on Windows, or /dev/ttyACM0 on Linux
    Attributes
    ----------
    rsc : serial
        The serial communication with the device
    port : str
        The port where the device is connected, such as COM3 or /dev/ttyACM0
    """

    DEFAULTS = {'write_termination': '\n',
                'read_termination': '\n',
                'encoding': 'ascii',
                'baudrate': 9600,
                'read_timeout': 1,
                'write_timeout': 1,
                }

    MAX_CHANNELS = 2

    def __init__(self, port):
        super().__init__()
        self.port = port

    def initialize(self):
        """
        Opens the serial port with the DEFAULTS.
        Returns
        -------
            None
        """
        self.rsc = serial.Serial(port=self.port,
                                 baudrate=self.DEFAULTS['baudrate'],
                                 timeout=self.DEFAULTS['read_timeout'],
                                 write_timeout=self.DEFAULTS['write_timeout'])
        sleep(0.5)
        self.beep()
        self.id = self.idn()
        print(f'({self.port}) Initialized resource:\n {self.id}')

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
        self._query('SYST:BEEP')

    def get_input(self, channel):
        """
        Get current reading
        Parameters
        ----------
        channel : int
            channel number

        Returns
        -------
            str answer containing the reading
        """
        message = 'IN:CH{}'.format(channel)
        ans = self._query(message)
        
        return ans

    def set_output(self, channel, output_value):
        """
        Set analog output on a channel
        Parameters
        ----------
        channel : int
            number of output channel
        output_value : int
            output value in the range 0-4095
        Returns
        -------
            None
        """
        message = 'OUT:CH{}:{}'.format(channel, output_value)
        self._query(message)

    def _write(self, message):
        """
        Write message to the resource
        Parameters
        ----------
        message : str
            message to be sent to the device
        Returns
        -------
            None

        """
        message = message + self.DEFAULTS['write_termination']
        message = message.encode(self.DEFAULTS['encoding'])
        self.rsc.write(message)

    def _read(self):
        """
        Read message from the resource
        Returns
        -------
            str message returned by device
        """
        # ans = self.rsc.readline() # readline() assumes \n as escape character causing read timeout on devices that
        # use any other read termination character.
        escape_char = bytes(self.DEFAULTS['read_termination'], self.DEFAULTS['encoding'])
        ans = self.rsc.read_until(escape_char) # ... this is why read_until is used
        #print(f'##### Raw answer is: {ans}') #debug only
        ans = ans.decode(self.DEFAULTS['encoding']).strip()
        return ans

    def finalize(self):
        """
        Closes the resource
        Returns
        -------
            None
        """
        if self.rsc is not None:
            self.rsc.close()
            self.rsc = None
            print(f'({self.port}) Released resource:\n {self.id}')

    def _arg_check(self, channels):
        """
        If channels is tuple it returns it without change. If channels is an int it places it inside a tuple.
        For any other type TypeError is raised.
        Parameters
        ----------
        channels : int or tuple

        Returns
        -------
            tuple
        """
        if isinstance(channels, tuple):
            pass
        elif isinstance(channels, int):
            channels = tuple([channels])
        else:
            raise TypeError(f'Incorrect argument type for channels ({channels})')

        for channel in channels:
            if channel > self.MAX_CHANNELS:
                raise ValueError(f'This device does not support channel {channel}')

        return channels


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

    def get_input(self, channel):
        """
        Get current reading
        Parameters
        ----------
        channel : int or tuple
            1 - gets primary display reading
            2 - gets secondary display reading
            (1,2) - will not raise errors but gets secondary reading only
        Returns
        -------
            tuple of strings with measurement reading and corresponding unit of measure
        """
        channels = self._arg_check(channel)
        for ch in channels:
            if ch == 1:
                reading_message = 'FETC?'
                unit_message = 'CONF?'
            elif ch == 2:
                reading_message = 'FETC? @3'
                unit_message = 'CONF? @3'
            else:
                raise TypeError(f'Device does not support channel {ch}.')

            reading = self._query(reading_message)
            unit = self._query(unit_message)

        # output format strongly depends on device type, more here: https://sigrok.org/wiki/Agilent_U12xxx_series

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

    def initialize(self):
        super().initialize()
        self._disengage_all_outputs()

    def get_input(self, channel):
        """
        Get voltage and current readings from a channel
        Parameters
        ----------
        channel : int or tuple
            channel number
        Returns
        -------
            tuple of strings containing the channel reading and corresponding units of measure
        """
        channel_set = self._arg_check(channel)

        for ch_nr in channel_set:
            # select channel
            self._write(f'INST:NSEL {str(ch_nr)}')
            # query measurements
            voltage = self._query('MEAS:VOLT?')
            current = self._query('MEAS:CURR?')

        return voltage, 'Volt', current, 'Amp'

    def set_output(self, channels, voltage=0.0, current=0.0):
        """
        Set output voltage and current limits at specific channel(s)

        NOTE: be careful when changing voltage and current settings when outputs are engaged. There may also be a time
        delay between setting voltage and current limit that can cause transient state which could be dangerous
        for your DUT.

        Parameters
        ----------
        channels : int or tuple
            channel number(s)
        voltage : float
            channel voltage limit in volts
        current : float
            channel current limit in ampere
        Returns
        -------
            None
        """
        channels = self._arg_check(channels)
        for ch in channels:
            # select the channel
            self._write(f'INST:NSEL {str(ch)}')
            # set output levels
            self._write(f"VOLT {str(voltage)}{self.DEFAULTS['write_termination']}CURR {str(current)}")  # TODO second write termination missing?

    def engage_output(self, channels, seek_permission=True):
        """
        Engage outputs on specific channels with user permission
        Parameters
        ----------
        channels : int or tuple
            channel or channels to be activated
        seek_permission : bool
            True - seek user permission before activating the outputs
            False - activate outputs without any permission (dangerous for your DUT!)
        Returns
        -------
            int 1 - output engage command sent
                0 - output engage command was not sent because user permission was not granted
        """
        channels = self._arg_check(channels)
        self.disengage_output()
        self._activate_channels(channels)
        for channel in channels:
            # select channel
            self._write(f'INST:NSEL {str(channel)}')
            # query output setting
            sel_voltage = self._query('VOLT?')
            sel_current = self._query('CURR?')
            print(f'Ch:{channel} is activated at:\n'
                  f' {sel_voltage} Volt\n'
                  f' {sel_current} Amp')

        if seek_permission:
            if input(f'Are you sure you want to engage outputs on active channels?\n Enter [y] to continue.\n') != 'y':
                self.disengage_output()
                return 0

        self._write('OUTP:GEN 1')
        return 1
        
    def _deactivate_channels(self, channels=tuple(range(1, MAX_CHANNELS+1))):
        """
        Deactivate all channels 'at once'.
        Parameters
        ----------
        channels - tuple
            numbers of channels
        Returns
        -------
            None
        """
        long_msg = []
        channels = self._arg_check(channels)
        for channel in channels:
            long_msg.append(f"INST:NSEL {str(channel)}{self.DEFAULTS['write_termination']}OUTP:SEL 0{self.DEFAULTS['write_termination']}")
            # TODO - a workaround to get the selected channels to shut down as much together as possible (separate
            #  queries can take long and that can lead to in-between outputs state that user may not expect).
            #  SCPI standard allows to separate commands with semicolon (;) to send more commands in a single message
            #  but this device does not seem to support that.
        self._write("".join(long_msg))
    
    def _activate_channels(self, channels=tuple(range(1, MAX_CHANNELS+1))):
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

    def disengage_output(self, channels='all'):
        """
        Disengage outputs on specif channels at once.
        Parameters
        ----------
        channels : int or tuple of integers
            number(s) of output channel(s) to disengage, when not passed all outputs will be disengaged
        Returns
        -------
            None
        """
        if channels is 'all':
            self._disengage_all_outputs()
        else:  # deactivate only the specific outputs
            self._deactivate_channels(channels)

    def _disengage_all_outputs(self):
        """
        Shuts down all outputs at once and subsequently deactivates all channels.
        Returns
        -------
            None
        """
        self._write('OUTP:GEN 0') # immediate shut down of all outputs
        self._deactivate_channels()

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

    def idn(self):
        """
        Query device identification number.
        Returns
        -------
            str identification of the device
        """
        self._query('ID')  # First portion of the message is just confirmation if query was understood (0 or 1)
        ans = self._read()  # Next part is the actual ID info
        return ans

    def get_input(self, channel=1):
        """
        Get current primary display reading.
        Parameters
        ----------
        channel : int or tuple
            1 - get primary display reading
                Currently only primary display reading is supported
        Returns
        -------
            tuple of strings with measurement reading and device specific representation of the unit
        """
        channels = self._arg_check(channel)
        for _ in channels:
            self._query('QM')
            ans = self._read()
            ans_list = [item.strip() for item in ans.split(',')]
            reading = ans_list[0]
            unit = ans_list[1]

        return reading, unit

    def set_output(self, channel, output_value):
        print(f'Device class {self.__class__.__name__} does not allow control of its output\n')


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

    def initialize(self):
        super().initialize()
        self._disengage_all_outputs()

    def get_input(self, channel):
        """
        Get voltage and current reading from a channel.
        Parameters
        ----------
        channel - int or tuple
            channel number
        Returns
        -------
            tuple of strings containing the measurement reading and corresponding unit of measure
        """

        voltage = self._query(f'V{str(channel)}O?')[:-1]
        current = self._query(f'I{str(channel)}O?')[:-1]

        return voltage, 'Volt', current, 'Amp'

    def set_output(self, channels, voltage=0.0, current=0.0):
        """
        Set output voltage and current limits at specific channel(s)

        NOTE: be careful when changing voltage and current settings when outputs are engaged. There may also be a time
        delay between setting voltage and current limit that can cause transient state which could be dangerous
        for your DUT.

        Parameters
        ----------
        channels : int or tuple
            channel number(s)
        voltage : float
            channel voltage limit in volts
        current : float
            channel current limit in ampere
        Returns
        -------
            None
        """
        # set output levels
        channels = self._arg_check(channels)
        for channel in channels:
            self._write(f'V{str(channel)} {str(voltage)};I{str(channel)} {str(current)}')

    def engage_output(self, channels, seek_permission=True):
        """
        Engage outputs on specific channels with user permission
        Parameters
        ----------
        channels : int or tuple
            output channel or channels to be engaged
        seek_permission : bool
            True - seek user permission before activating the outputs
            False - activate outputs without any permission (dangerous for your DUT!)
        Returns
        -------
        int 1 - output engage command sent,
            0 - output engage command was not sent because user permission wasn't granted
        """
        long_msg = []
        chan_support_msg = ''
        channels = self._arg_check(channels)
        self.disengage_output()

        for channel in channels:

            # query output setting
            sel_voltage = self._query(f'V{str(channel)}?')[3:] # The response is V <n> <nr2> where <nr2> is in Volts
            sel_current = self._query(f'I{str(channel)}?')[3:]

            if sel_voltage == '':
                chan_support_msg = ' Device does not seem to support this channel'

            print(f'Ch:{channel} is set to:\n'
                  f' {sel_voltage} Volt\n'
                  f' {sel_current} Amp\n'
                  f' {chan_support_msg}')

            long_msg.append(f'OP{str(channel)} 1;')

        if seek_permission:
            if input(f'Are you sure you want to engage outputs on these channels?\n Enter [y] to continue.\n') != 'y':
                self.disengage_output()
                return 0

        self._write("".join(long_msg))
        return 1

    def disengage_output(self, channels='all'):
        """
        Disengage outputs on specif channels at once.
        Parameters
        ----------
        channels : int or tuple of integers
            number(s) of output channel(s) to disengage, when not passed all outputs will be disengaged
        Returns
        -------
            None
        """
        if channels is 'all':
            self._disengage_all_outputs()
        else:  # deactivate only the the specific outputs, all at once
            channels = self._arg_check(channels)
            long_msg = []
            for channel in channels:
                long_msg.append(f'OP{str(channel)} 0;')
                
            self._write("".join(long_msg))

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
                'write_termination': ' />',  # TODO: check if space is really needed
                'encoding': 'ascii',
                "HOST": "127.0.0.1",
                "PORT": 12001,
                "read_buffer": 32768,
                "meas_request": 'request name="measure" beep="on" mode="direct" integration_time="5000" '
                                'repeat_count="1" auto="on"'}  # with auto="on" integration_time is ignored.

    # HOST: Standard loopback interface address
    # PORT: Same port that GL SPECTROSOFT establishes (use netstat in case its different in case of your equipment)

    def __init__(self):

        super().__init__()
        # Remind user to install socket to use this model:
        if socket is None:
            raise ImportError(f'{self.__class__.__name__} requires module "socket", which failed on import with '
                              f'error:\n{exc1}')

        self.xml_dump_file_name = None  # if overwritten with str file dumping with that str in file name as prefix
        # will be dumped for every measurement. If user specifies any other type it will be ignored.
        # TODO: implement as _xml... and set up decorated setter and getter with @property and
        #  @xml_dump_file_name.setter, although at this point it appears as unnecessary boilerplate...

    def initialize(self):

        # Simple TCP server setup with blocking handshake:
        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listen_socket.bind((self.DEFAULTS['HOST'], self.DEFAULTS['PORT']))
        listen_socket.listen()
        print('Host {self.HOST} waiting for GL TOUCH Device at PORT {self.PORT}')
        print('In order for the application to proceed please ensure that the TOUCH device is powered up '
              'and physically connected to the local host.')
        tcp_conn_socket, client_address = listen_socket.accept()
        print(f'TCP Server Host {self.DEFAULTS["HOST"]} established connection with measurement device at:\n '
              f'{client_address}.')

        self.id = client_address[0]
        self.port = client_address[1]
        self.rsc = tcp_conn_socket

    def _write(self, message):
        message = self.DEFAULTS['write_prefix'] + message + self.DEFAULTS['write_termination']
        message = message.encode(self.DEFAULTS['encoding'])
        self.rsc.sendall(message)

    def _read(self):
        # data returned by recv is readily an xml format string
        gl_xml_string = self.rsc.recv(self.DEFAULTS['read_buffer'])
        return self._parse_xml_to_dict(gl_xml_string, xml_dump=self.xml_dump_file_name)

    def get_input(self, *args):
        """ Trigger and return measurement output in form of results dictionary

        Parameters
        ----------
        *args : int channel - optional channel argument (here unused)
        """
        return self._query(self.DEFAULTS['meas_request'])

    def set_output(self, *args):
        """

        Parameters
        ----------
        args : tuple (int channel, any output_parameters) optional parameters (here unused)

        Returns
        -------

        """
        raise NotImplementedError(f'This is not implemented. If you wish to change the measurement parameters you can '
                                  f'modify the DEFAULTS[meas_request] string attribute values. Currently '
                                  f'these attributes are set to {self.DEFAULTS["meas_request"]}')
        # TODO The measurement message could be modified by this interface without any actual communications here.

    @staticmethod
    def _parse_xml_to_dict(xml_string, xml_dump=False):
        root = et.fromstring(xml_string)

        if type(xml_dump) is str:
            date_str = datetime.now().strftime("%Y_%m_%d_%H%M%S")
            file_name = xml_dump.strip('.xml') + date_str + '.xml'
            et.ElementTree(root).write(file_name)

        results_dict = dict()
        for parameter in root.find('results'):
            results_dict[parameter.attrib.get('name')] = parameter.text

        # TODO this can be dict of dicts each containing the contents from each of the tags. E.g. meas_dict['status'][
        #  x], meas_dict['data'][x], meas_dict['results'][x].

        # TODO some of the items under 'results' have non obvious name attribute. Perhaps their content can be copied
        #  to additional entries with more friendly names (e.g. results_dict["Y"] = results_dict["luminous_flux"]),
        #  also one level deeper some static definitions of units can be added i.e.: results_dict["luminous_flux"][
        #  'unit'] since these are terribly missing in the xml returned by the device.

        return results_dict

if __name__ == '__main__':

    pass
    # AGILENT DMM TESTING STARTS HERE
    
    # dmm1 = AgilentU12xxxDmm('COM9') #<---- Remember to change the port
    # dmm1.initialize()
    # print(f'Device class{dmm1.__class__.__name__} ({dmm1.port})\n ID: {dmm1.id}\n')
    #
    # primary_reading, primary_units = dmm1.get_input(1)
    # secondary_reading, secondary_units = dmm1.get_input(2)
    #
    # print(f' CH1_READING:{primary_reading} {primary_units}\n CH2_READING:{secondary_reading} {secondary_units}\n')
    # dmm1.finalize()
    
    # ROHDE PSU DEMO STARTS HERE

   # psu1 = RohdeHmp4ChPsu('COM12')
   # psu1.initialize()
   # print(f'Device class {psu1.__class__.__name__} ({psu1.port})\n ID: {psu1.id}\n')
   #
   # psu1.set_output(1,voltage=1, current=0.555)
   # psu1.set_output(2,voltage=2, current=0.556)
   # psu1.set_output(3,voltage=3, current=0.557)
   # psu1.set_output(4,voltage=4, current=0.558)
   #
   # psu1.engage_output(1) # you will be prompted if you really wish to continue under current settings
   # sleep(2)
   #
   # psu1.engage_output(2) #repeating request will cause all other channels to reset (shut down).
   # sleep(2)
   #
   # psu1.engage_output((1, 2, 3)) # all channel outputs in the tuple will engage at the same instance
   # sleep(2)
   #
   # for chanel in (1, 2, 3, 4):
   #     volts, v_unit, current, i_unit = psu1.get_input(chanel)
   #     print(f' Ch:{chanel} reading:{volts}{v_unit} and {current}{i_unit}\n')
   #
   # psu1.disengage_output((1, 2, 3)) # channels should disengage pretty much at the same instance
   # sleep(2)
   #
   # psu1.engage_output((1, 2))
   # sleep(2)
   #
   # psu1.set_output(1, voltage=2, current=1) # NOTE: you can manipulate output settings on an engaged output.
   # Do so at your own risk!
   #
   # psu1.disengage_output() # this definitely, immediately shuts down all channels simultaneously
   # psu1.finalize()
   #
   #  FLUKE DMM DEMO STARTS HERE
   #
   # dmm2 = Fluke28xDmm('COM13') #<---- Remember to change the port
   # dmm2.initialize()
   # print(f'Device class{dmm2.__class__.__name__} ({dmm2.port})\n ID: {dmm2.id}\n')
   #
   # reading, units = dmm2.get_input()
   #
   # print(f' CH1_READING:{reading} {units}\n')
   # dmm2.finalize()
   #
   #  Tti3ChPsu DEMO STARTS HERE
   #
   # psu2 = Tti3ChPsu('COM10')
   # psu2.initialize()
   # sleep(2)
   # psu2.set_output(1,voltage=1,current=0.1)
   # psu2.set_output(2,voltage=2,current=0.2)
   # sleep(2)
   # psu2.engage_output((1,2))
   # sleep(2)
   # print(psu2.get_input(1))
   # sleep(2)
   # psu2.disengage_output(2)
   # sleep(2)
   # psu2.disengage_output()
   # sleep(2)
   # psu2.finalize()
    
