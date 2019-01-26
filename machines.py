#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Created Tue 24 Jan 16:05:00 2019

@author:rday

"""
import visa


rm = visa.ResourceManager()

class HP3478A:
    
    def __init__(self,HPIB_address):
        
        self.address = 'GPIB0::{:d}::INSTR'.format(HPIB_address)
        self.instrument = self._connect()
        
        
    def _connect(self):
        
        return rm.open_resource(self.address)
    
    
    def _read_screen(self):
        
        print(self.instrument.query("*IDN?"))
        
        
        
    def _disconnect(self):
        
        print('disconnect')
        
    def _do_acv_measure(self):
        '''
        AC voltage measurement (F2)
        Autorange (RA)
        Autozero on (Z1)
        4.5 digits (N4) -- F2RAZ1N4: returns an ac voltage measurement
        '''
        return float(self.instrument.query("F2RAZ1N4"))
    
    
    
    
    
class LS331:
    
    def __init__(self,GPIB_address,channel):
        
        self.address = 'GPIB0::{:d}::INSTR'.format(GPIB_address)
        self.channel = channel
        self.instrument = self._connect()
        
    def _connect(self):
        
        return rm.open_resource(self.address)
        
        
    def _disconnect(self):
        
        print('disconnecting from LS331')
        
        
    def _measure_T(self):
        
        return float(self.instrument.query('KRDG? {:s}'.format(self.channel)))


class SR850:
    
    def __init__(self,GPIB_address):
        
        self.address = GPIB_address
        
        
    def _connect(self):
        
        print('connecting to SR850')
        
        
    def _disconnect(self):
        
        print('disconnecting from SR850')
    
    
    def _measure_V(self):
        
        print('measuring')
        return 0
    
    
    