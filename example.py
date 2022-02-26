# -*- coding: utf-8 -*-
"""
Created on Tue Oct 12 10:22:10 2021

@author: MJABLONS
"""

from serial_controllers import AgilentU12xxxDmm, Tti2ChPsu, GlOpticTouch, Fluke28xDmm, RohdeHmp4ChPsu
from time import sleep
import pprint

AGILENT_DMM_COM = 'COM17'
TTI_2CH_PSU_COM = 'COM10'
FLUKE_DMM_COM = 'COM13'
ROHDE_4CH_PSU_COM = 'COM12'


def agilent_dmm_example():
    
    dmm = AgilentU12xxxDmm(AGILENT_DMM_COM) #<-- Remember to change the port
    ## Not sure which port name to type in?
    ## Try this script! -> https://github.com/mjablons1/scpi-hw-discovery
    dmm.initialize()
    
    primary_reading, primary_unit = dmm.get_input(1)
    secondary_reading, secondary_unit = dmm.get_input(2)
    
    print(f' CH1_READING:{primary_reading} {primary_unit}\n CH2_READING:{secondary_reading} {secondary_unit}\n')
    dmm.finalize() # releases serial resource
    
def fluke_dmm_example():
    
    dmm = Fluke28xDmm(FLUKE_DMM_COM) #<-- Remember to change the port
    ## Not sure which port name to type in?
    ## Try this script! -> https://github.com/mjablons1/scpi-hw-discovery
    dmm.initialize()
    
    primary_reading, primary_unit = dmm.get_input(1)
    
    print(f' CH1_READING: {primary_reading} {primary_unit}\n')
    dmm.finalize() # releases serial resource    



def tti_2_ch_psu_example():
    psu = Tti2ChPsu(TTI_2CH_PSU_COM) #<-- Remember to change the port
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
    
    
def rohde_4_ch_psu_example():
    psu = RohdeHmp4ChPsu(ROHDE_4CH_PSU_COM) #<-- Remember to change the port
    ## Not sure which port name to type in?
    ## Try this script! -> https://github.com/mjablons1/scpi-hw-discovery
    psu.initialize()
    
    psu.set_output(1, voltage=1.2, current=0.01)
    psu.set_output(2, voltage=2.2, current=0.02)
    
    psu.engage_output((1, 2)) # engages output on channel 1 and 2 after user approval
    sleep(2)
    
    psu.disengage_output(2) # disengages only output 2 (output 1 remains engaged)
    sleep(2)
    
    psu.engage_output(2, seek_permission=False) # after this only channel 2 will be engaged and without user approval!
    sleep(2)
    
    volts, v_unit, current, i_unit = psu.get_input(2)
    print(f'Reading:{volts}{v_unit} and {current}{i_unit}\n')
    
    psu.set_output(2, voltage=3, current=0.03) # WARNING!: You can manipulate levels on engaged output.
    
    psu.disengage_output() # this immediately shuts down all engaged channels simultaneously
    psu.finalize() # releases serial resource
    
def spectis_example():
    spectr = GlOpticTouch()
    spectr.initialize()
    res = spectr.get_input()
    pprint.pprint(res)
    spectr.finalize()
    
if __name__ == '__main__':
    
    #tti_2_ch_psu_example() # ok
    #spectis_example() # ok
    #fluke_dmm_example() # ok
    #agilent_dmm_example() # ok
    #rohde_4_ch_psu_example() # ok
