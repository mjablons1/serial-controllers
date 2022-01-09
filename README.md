# serial-controllers
Several basic controller classes for serial hardware such as DMMs (Digital Multimters) and PSUs (Power Supplies).
## Functionality
The controller classes support only the most basic and routinely used functionality such as get_input (returns current reading), and set_output (configures output limits on PSUs):
## Example DMM use

```python
from serial_controllers import AgilentU12xxxDmm

dmm = AgilentU12xxxDmm('COM9') #<-- Remember to change the port
## Not sure which port name to type in?
## Try this script! -> https://github.com/mjablons1/scpi-hw-discovery
dmm.initialize()

primary_reading, primary_unit = dmm.get_input(1)
secondary_reading, secondary_unit = dmm.get_input(2)

print(f' CH1_READING:{primary_reading} {primary_unit}\n CH2_READING:{secondary_reading} {secondary_unit}\n')
dmm.finalize() # releases serial resource
```

## Example PSU use

```python
from serial_controllers import Tti2ChPsu
from time import sleep

psu = Tti2ChPsu('COM10') #<-- Remember to change the port
## Not sure which port name to type in?
## Try this script! -> https://github.com/mjablons1/scpi-hw-discovery
psu.initialize()

psu.set_output(1, voltage=1.2, current=0.01)
psu.set_output(2, voltage=2.2, current=0.02)

psu.engage_output((1, 2)) # engages output on channel 1 and 2 after user approval
sleep(2)

psu.disengage_output(1) # disengages only output 1 (output 2 remains engaged)
sleep(2)

psu.engage_output(2, seek_permission=False) # after this only channel 2 will be engaged and without user approval!
sleep(2)

volts, v_unit, current, i_unit = psu.get_input(2)
print(f'Reading:{volts}{v_unit} and {current}{i_unit}\n')

psu.set_output(2, voltage=3, current=0.03) # WARNING!: You can manipulate levels on engaged output.

psu.disengage_output() # this immediately shuts down all engaged channels simultaneously
psu.finalize() # releases serial resource
```

## Currently supported devices 
NOTE: Some versions of below devices may require adjustments due to inconsistencies in the protocols.
### Multimeters (DMMs):

| Brand         | Model           | serial-controllers supporting class | Verified with | Comments |
| ------------- |:---------------:| -----------------------------------:| ------------: | -------: |
| Keysight / Agilent | U12xxx | AgilentU12xxxDmm | Keysight U1253B | |
| Fluke | 28x | Fluke28xDmm | Fluke 289 | |

### Power Supplies (PSUs):

| Brand         | Model           | serial-controllers supporting class | Verified with | Comments |
| ------------- |:---------------:| -----------------------------------:| ------------: | -------: |
| TTI | CPX400DP | Tti2ChPsu| * | |
| TTI | CPX400SP | Tti1ChPsu| | |
| TTI | PL155-P(G) | Tti1ChPsu | * | |
| TTI | PL068-P(G)| Tti1ChPsu | | |
| TTI | PL303-P(G) | Tti1ChPsu | | |
| TTI | PL601-P(G) | Tti1ChPsu | | |
| TTI | PL303QMD-P(G) | Tti2ChPsu | | |
| TTI | PL303QMT-P(G) | Tti3ChPsu | | |
| TTI | EL302P-USB | N.A. | | not supported |
| TTI | EX355P-USB | N.A. | | not supported |
| TTI | QL355TP | TtiQL2ChPsu | | operates at 19200 baud rate by default |
| TTI | QL355P | TtiQL1ChPsu | | operates at 19200 baud rate by default |
| TTI | QL564TP | TtiQL2ChPsu | | operates at 19200 baud rate by default |
| TTI | QL564P | TtiQL1ChPsu | | operates at 19200 baud rate by default |
| Rohde & Schwarz | HMP2030 | RohdeHmp3ChPsu | | |
| Rohde & Schwarz | HMP4040 | RohdeHmp4ChPsu | * | |

### Spectrometers:

| Brand         | Model           | serial-controllers supporting class | Verified with | Comments |
| ------------- |:---------------:| -----------------------------------:| ------------: | -------: |
| GL Optic | Touch 1.0 | GlOpticTouch | * | Requires GL Spectrosoft PRO which runs a TCP server that relays the measurement data from the spectrometer. See HW manuals/gl_parsing_result.txt for example dict structure returned by get_input().|
    
## Acknowledgements
1) The base class relies on a modified SimpleDaq class from Python For the Lab materials. [link to source](https://github.com/aquilesC/SimpleDaq/blob/master/PythonForTheLab/Controller/simple_daq.py)
2) Sigrok website where lots of devices protocols are reverse-engineered. Beautiful middle finger solution in case your hw supplier refuses to cooperate. [Sigrok homepage](https://sigrok.org/wiki/Main_Page)
    

