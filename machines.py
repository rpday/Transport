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
        
        self.instrument.before_close()
        self.instrument.close()
        
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
        
        self.instrument.before_close()
        self.instrument.close()
        
        
    def _measure_T(self):
        Tnow = self.instrument.query('KRDG? {:s}'.format(self.channel))
        return float(Tnow)


class SR850:
    
    def __init__(self,GPIB_address,freq=27.2,Vin=1.0):
        
        self.address = 'GPIB::{:d}::INSTR'.format(GPIB_address)
        self.instrument = self._connect()
        self._instrument_setup(freq,Vin)
        
    def _connect(self):
        
        return rm.open_resource(self.address)
    
    def _instrument_setup(self,freq,Vin):
        self.instrument.write('FMOD 0',termination='<lf>')
        self.instrument.write('FREQ {:0.03f}'.format(freq),termination='<lf>')
        self.instrument.write('SLVL {:0.03f}'.format(Vin),termination='<lf>')
        self.instrument.write('STRT',termination='<lf>')
        
        
        
        
    def _disconnect(self):
        
        self.instrument.before_close()
        self.instrument.close()
    
    
    def _measure_V(self):
        
        x = float(self.instrument.query('OUTP? 1'))
        y = float(self.instrument.query('OUTP? 2'))
        return x,y
    
    
    