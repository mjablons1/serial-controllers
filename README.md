# serial-controllers
Several basic controller classes for serial hardware such as DMMs (Digital Multimters) and PSUs (Power Supplies).
## Functionality
The controller classes support only the most basic and routinely used functionality such as get_input (returns current reading), and set_output (configures output limits on PSUs):
## Example DMM use

```python
from serial_cntrollers import AgilentU12xxxDmm

dmm1 = AgilentU12xxxDmm('COM9') #<-- Remember to change the port
dmm1.initialize()

primary_reading, primary_units = dmm1.get_input(1)
secondary_reading, secondary_units = dmm1.get_input(2)

print(f' CH1_READING:{primary_reading} {primary_units}\n CH2_READING:{secondary_reading} {secondary_units}\n')
dmm1.finalize()
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
    
## Acknowledgements
1) The base class relies on a modified SimpleDaq class from Python For the Lab materials. [link to source](https://github.com/aquilesC/SimpleDaq/blob/master/PythonForTheLab/Controller/simple_daq.py)
2) Sigrok website where lots of devices protocols are reverse-engineered. Beautiful middle finger solution in case your hw supplier refuses to cooperate. [Sigrok homepage](https://sigrok.org/wiki/Main_Page)
    

