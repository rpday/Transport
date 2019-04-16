# -*- coding: utf-8 -*-
"""
Created on Mon Apr 15 14:54:13 2019

@author: rday
"""

import matplotlib.pyplot as plt
import numpy as np

import tkinter as Tk
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from threading import Thread
from queue import Queue
import time




class interface:
    '''
    This GUI is intended for interaction with user running a transport measurement
    with the XPS cryostat. The user selects a temperature setpoint, a resistance sampling
    time (in seconds), and a resistance sampling interval (in Kelvin). In the future,
    it would be nice to allow for a pop-up with a more sophisticated programming option, 
    including not just one cycle with measurements, but dwells, heating and cooling, etc.
    We make use of multiple threads to allow the system to perform several time-consuming
    processes (such as resistance measurements) and temperature readings, while maintaining 
    user and PC access to the main GUI thread. 
    
    To do:
        
        - active plot window: currently have placeholder box
            - include zoom functionality
        - print current resistance to display (for sample and reference)
        - readout to file (implemented in ubc_resistivity already)
        - connect with machines.py to implement actual machine queries
        - connect to actual machines and test functionality with GPIB on a single port, given
            asynchronous queries to Lakeshore, Keithley, and SRS
        - do an actual measurement!
        
        
    '''
    def __init__(self):
        self.running = False
        self.run_temp = False
        self.dwell = False
        self.acquiring = False
        self.queue = Queue()
        self.tempnow = 300.0
        self.setnow = 300.0
        self.rate = 1.0
        self.integrate = 10.0
        
        self.Tsample = []
        self.Rsample = []
        self.Rref = []
        self.time_record = []
        
        self.temp_tol = 0.5
        self.stable_tol = 2.0
        self.dwell_time = 0.0
        self.measure_time = 0.0
        
        self.cycle = 'Idle'
        self.window_make()
        
                                    
                        
###############################################################################
########################                    ###################################
########################    THREAD SETUP    ###################################
########################                    ###################################
###############################################################################        
        
    def initialize_timekeeper(self):
        '''
        Set the timekeeper thread running. This can only be started once,
        and the boolean flags required to safely exit this thread upon 
        closing the interface are defined here as well.
        '''
        self.run_timer  = True
        self.stop_timer = False
        self.timethread = Thread(target = self.time_update)
        self.timethread.setDaemon(True)
        self.timethread.start()
        
    def initialize_thermometer(self):
        '''
        Set the thermometer thread running. This can only be started once,
        and the boolean flags required to safely exit this thread upon 
        closing the interface are defined here as well.
        '''
        
        self.run_temp = True
        self.stop_temp = False
        self.T_thread = Thread(target = self.temp_update)
        self.T_thread.setDaemon(True)
        self.T_thread.start()
        
    def initialize_resistance(self):
        '''
        Set the resistance thread running. This can only be started once,
        and the boolean flags required to safely exit this thread upon 
        closing the interface are defined here as well.
        '''
        
        self.run_res = True
        self.stop_res = False
        self.R_thread = Thread(target = self.res_update)
        self.R_thread.setDaemon(True)
        self.R_thread.start()
        
        
    def time_update(self):
        '''
        Time-keeper updates the program time once a second, on its own thread,
        allowing the interface to remain accessible to the user, while the
        counter is being incremented. This timestamp can be referenced by any
        of our other worker-threads, such as the temperature logger, to dictate 
        when a new job should be submitted to the queue. This is set, by default,
        to update every 100 ms.
        '''
        while self.run_timer:
            tnow = time.time()
            self.time_stamp = tnow
            self.timestring.set(time.ctime(self.time_stamp))
            if self.running:
                if np.mod(self.time_stamp-self.time_start,5)<1:
                    self.update_plot()
            time.sleep(1)
            
            if self.stop_timer:
                break
            
    def temp_update(self):
        '''
        Main worker function for the temperature thread--besides the ongoing
        time loop, this function determines the state of progress, using the 
        logic network of *cycle_update* below. While the daemon is in principle
        running this function continuously, it only really executes when the 
        program is in its 'running' mode, i.e. the start button has been pressed.
        '''
        
        while self.run_temp:

            if self.running:
                self.tempnow = self.measure_temp()
                self.cycle_update()
                self.tempnow_str.set('Temperature: {:0.03f}'.format(self.tempnow))

            if self.stop_temp:
                break
            
    def res_update(self):
        '''
        Main worker function for the resistance measurement-thread. As with temp_update,
        this is constantly running, but only actually executes the measurement when we 
        are in acquistion mode, set by *cycle_update*
        '''
        
        while self.run_res:
            
            if self.running and self.acquiring:
                self.resnow = self.measure_R()
                self.Tmeasurement.append(self.tempnow)
                self.Rmeasurement.append(self.resnow)
                print('Resistance: ',self.resnow)
            
            if self.stop_res:
                break
        
###############################################################################
##########################                     ################################
########################## ACQUISITION PROGRAM ################################
##########################                     ################################
###############################################################################   
        
            
    def update_program(self):
        try:
            self.setnow = float(self.set_var.get())
        except ValueError:
            print('WARNING: MUST ENTER NUMERIC SETPOINT!')
            self.setnow = 300.0
        try:
            self.rate = float(self.rate_var.get())
        except ValueError:
            print('WARNING: MUST ENTER NUMERIC RATE!')
        try:
            self.integrate = float(self.int_var.get())
        except ValueError:
            print('WARNING: MUST ENTER A NUMERIC INTEGRATION TIME!')
            
        
        self.setnow_str.set('Setpoint: {:0.03f} K'.format(self.setnow))
        self.tempnow_str.set('Temperature: {:0.03f} K'.format(self.tempnow))
            
    
    def start_timers(self):
        '''
        If the user stops and starts acquisition, timers should be restarted, 
        to avoid hanging.
        
        '''
        self.time_start = time.time()
        self.measure_time = 0.0
        self.dwell_time = 0.0
    
    def cycle_run(self):
        
        '''
        Command upon press of the RUN/END button. The program controls are
        de-activated during acquisition, the timers are re-zeroed, and the 
        *running* boolean flag is set going--this activates the full execution
        of the thermometer and resistance (along with satisfied temperature stability)
        threads. Outside this operation, the user has access to program controls.
        '''
        
        self.running = not self.running
        if self.running:
            self.start_timers()        
                
            self.update_program()
            self.run_str.set('END')
            self.setpoint_set.config(state = 'disabled')
            self.rate_set.config(state = 'disabled')
            self.integrate_set.config(state = 'disabled')
            self.browse.config(state = 'disabled')
        else:
            self.cycle = 'Idle'
            self.cycle_str.set('Cycle: {:s}'.format(self.cycle))
            self.run_str.set('RUN')
            self.setpoint_set.config(state = 'normal')
            self.rate_set.config(state = 'normal')
            self.integrate_set.config(state = 'normal')
            self.browse.config(state = 'normal')
            
            
###############################################################################
############################              #####################################
############################ MEASUREMENTS #####################################
############################              #####################################
###############################################################################
            
            
            
    def measure_temp(self):
        '''
        Garbage function, generates fake temperature data, for use in designing the GUI ONLY
        '''
        
        Tnow = 250+5*np.exp(-(self.time_stamp-self.time_start)/5) + 0.05*np.random.random()
        time.sleep(0.2)
        return Tnow
        
            
    def measure_R(self):
        '''
        Dummy function right now, should be replaced by a proper call to the lock-in amplifier
        Simulates a dataread with a time sleep, and the just returns 1 with a 10% random error.
        '''
        
        
        time.sleep(1)
        return np.random.random()*0.5+5.0
        
            
    def cycle_update(self):
        '''
        This function defines a series of logic gates which determine the current state
        of the program. If temperature is changing, we print out to screen the current 
        cooling/heating state, if it is reasonably stable, we are either in the dwell
        or acquisition state. Once the dwell has been successfuly completed, without 
        ever leaving the safe range, then we initiate acquisition.
        
        '''
        
            
        if self.running:
            if abs(self.tempnow-self.setnow)>self.temp_tol:
                
                self.dwell = False 
                self.acquiring = False
                
                if self.tempnow>self.setnow:
                    self.cycle = 'Cooling'
                    
                elif self.tempnow<self.setnow:
                    self.cycle = 'Heating'

            else:
                if not self.dwell:
                    self.dwell_start = self.time_stamp
                    self.dwell = True
                else:
                    self.dwell_time = self.time_stamp - self.dwell_start
                    
                if self.dwell_time<self.stable_tol:
                    self.cycle = 'Stabilizing'
                else:
                    if not self.acquiring:
                        self.acquire_start = self.time_stamp
                        self.acquiring = True
                        self.Tmeasurement = []
                        self.Rmeasurement = []
                    self.measure_time = self.time_stamp-self.acquire_start
                    
                    if self.measure_time<self.integrate:
                        self.cycle = 'Acquiring'
                    else:
                        self.tidy_measurement()
                        print('change setpoint')
                        self.cycle = 'Continue'
        else:
            self.cycle = 'Idle'
            
        self.cycle_str.set('Cycle: {:s}'.format(self.cycle))
        
    def tidy_measurement(self):
        if len(self.Rmeasurement)>0:

            self.T_meas = sum(self.Tmeasurement)/len(self.Tmeasurement)
            self.R_meas = sum(self.Rmeasurement)/len(self.Rmeasurement) 
            self.Tsample.append(self.T_meas)
            self.Rsample.append(self.R_meas)
            
            self.time_record.append(self.time_stamp)
#            self.update_plot()
        self.acquiring = False
        self.dwell = False
        
    def update_plot(self):
        self.ax.cla()
        self.line, = self.ax.plot(self.time_record,self.Rsample)
        self.fig.canvas.draw()
        
###############################################################################
############################              #####################################
############################ WINDOW SETUP #####################################
############################              #####################################
###############################################################################       
        
            
                
    def make_program_frame(self):
        '''
        Create all requisite widgets for defining the execution program
        '''
        
        self.set_var = Tk.StringVar()
        self.set_var.set('{:0.03f}'.format(self.setnow))
        self.rate_var = Tk.StringVar()
        self.rate_var.set('{:0.03f}'.format(self.rate))
        self.int_var = Tk.StringVar()
        self.int_var.set('{:0.03f}'.format(self.integrate))
        self.program_frame = Tk.LabelFrame(master=self.root,text='Program',width=300)
        self.program_frame.grid(padx=10,row=6,column=0,sticky='W',pady=5,ipadx=5)
        self.setpoint_label = Tk.Label(master=self.program_frame,text='Setpoint: (K)').grid(row=7,column=0,sticky='W',pady=5)
        self.setpoint_set = Tk.Entry(master=self.program_frame,textvariable=self.set_var)
        self.setpoint_set.grid(row=7,column=2,columnspan=3,sticky='W',pady=5,ipadx=5)
        self.rate_label = Tk.Label(master=self.program_frame,text='Temperature Rate: (K/min)').grid(row=8,column=0,sticky='W',pady=5)
        self.rate_set = Tk.Entry(master=self.program_frame,textvariable=self.rate_var)
        self.rate_set.grid(row=8,column=2,columnspan=3,sticky='W',pady=5,ipadx=5)
        self.integrate_label = Tk.Label(master=self.program_frame,text='Date Integration: (s)').grid(row=9,column=0,sticky='W',pady=5)
        self.integrate_set = Tk.Entry(master=self.program_frame,textvariable=self.int_var)
        self.integrate_set.grid(row=9,column=2,columnspan=3,sticky='W',pady=5,ipadx=5)
        self.savelabel = Tk.Label(master=self.program_frame,text='Save: ').grid(row=10,column=0,sticky='W',pady=5)
        self.browse = Tk.Button(master=self.program_frame,text='Browse',command=self.browsefile)
        self.browse.grid(row=10,column=2,columnspan=3,sticky='W',ipadx=42,pady=5)
            
    
    def make_execute_frame(self):
        '''
        Set up all relevant widgets fo the execution, which will display live
        readout of temperature, setpoint, and current program objective.
        '''
        
        self.tempnow_str = Tk.StringVar()
        self.setnow_str = Tk.StringVar()
        self.cycle_str = Tk.StringVar()
        self.run_str = Tk.StringVar()
        self.tempnow_str.set('Temperature: {:0.03f} K'.format(self.tempnow)) ###UPDATE
        self.setnow_str.set('Setpoint: {:0.03f} K'.format(self.setnow))
        self.cycle_str.set('Cycle: {:s}'.format(self.cycle))
        self.run_str.set('RUN')
        
        self.running_frame = Tk.LabelFrame(master=self.root,text='Execution',width=300)
        self.running_frame.grid(padx=10,row=11,column=0,sticky='W',pady=5,ipadx=5)
        self.tempnow_label = Tk.Label(master=self.running_frame,textvariable=self.tempnow_str).grid(row=12,column=0,sticky='W',pady=5)
        self.setnow_label = Tk.Label(master=self.running_frame,textvariable=self.setnow_str).grid(row=13,column=0,sticky='W',pady=5)
        self.cycle_label = Tk.Label(master=self.running_frame,textvariable=self.cycle_str).grid(row=14,column=0,sticky='W',pady=5)
        
        self.run_button = Tk.Button(master=self.running_frame,textvariable=self.run_str,command=self.cycle_run,width=35)
        self.run_button.grid(row=15,column=0,padx=13,pady=5,columnspan=3)
        
    def browsefile(self):
        self.fnm =  filedialog.asksaveasfilename(initialdir = "/",title = "Select file",filetypes = (("text files","*.txt"),("all files","*.*")))
        
        if self.fnm[-4:]!='.txt':
            self.fnm = self.fnm+'.txt'
        
        
    def _quit(self):
        '''
        Quit the UI. To safely exit, the timekeeper and all other worker threads must
        safely be terminated, before then finally terminating the UI itself.
        '''
        if self.run_timer:
            self.stop_timer = True
            self.timethread.join()
        if self.run_temp:
            self.stop_temp = True
            self.T_thread.join()
        if self.run_res:
            self.stop_res = True
            self.R_thread.join()
        with self.queue.mutex:
            self.queue.queue.clear()
        self.root.quit()
        self.root.destroy()
        
    def fig_build(self):
        self.fig = plt.Figure(figsize=(6,4))
        self.ax = self.fig.add_subplot(111)
        self.line, = self.ax.plot(self.time_record,self.Rsample)
        self.window = FigureCanvasTkAgg(self.fig,master=self.root)
        self.window.get_tk_widget().grid(row=0,column=0,columnspan=8,rowspan=6)
        
    def window_make(self):
        '''
        Main executable for the Tkinter UI. This UI allows the user to set-up and
        acquire a data acquisition on the transport cryostat. The user chooses 
        a cooling/heating rate, a sampling time, and a sampling rate (in units of K)
        '''
        
        self.root = Tk.Tk()
#        self.root.geometry('315x620')
        self.timestring = Tk.StringVar()
        self.timestring.set(time.ctime(time.time()))
        
        self.initialize_timekeeper()
        
        self.initialize_thermometer()
        self.initialize_resistance()
        
    

#        self.dataplot = Tk.Canvas(master=self.root)
#        self.dataplot.create_rectangle(10, 10, 303, 290, outline="#fb0", fill="#fb0")
#        self.dataplot.grid(row=0,column=0,columnspan=6,rowspan=6,sticky='W')
        self.fig_build()
        self.make_program_frame()
               
        self.make_execute_frame()       
        
        self.qbutton = Tk.Button(master=self.root,text='QUIT',command=self._quit)
        self.qbutton.grid(row=16,column=0,sticky='W',pady=5,padx=10)
        
        self.time_label = Tk.Label(master=self.root,textvariable=self.timestring).grid(row=16,column=0,sticky='E',ipadx=20)

        
        Tk.mainloop()
        
        
        
        
if __name__ == "__main__":
    
    interface()
        