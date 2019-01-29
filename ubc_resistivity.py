#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Created Tue 24 Jan 14:12:00 2019

@author:rday

"""


import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FormatStrFormatter
import numpy as np
import datetime
import tkinter as Tk
from tkinter import filedialog

import machines


class interface:

    def __init__(self):
        self.running = False
        #        self.sample,self.user,self.material,self.Rr,self.amplification = self._get_info()

        self.fnm = 'Sample_001.txt'
        self.sample = 'Sample'
        self.user = 'Username'
        self.material = 'Material'
        self.Rr = 1.0e4
        self.amplification = 1.0e2
        
        self.voltmeter = machines.HP3478A(9)
        self.lakeshore = machines.LS331(15,'A')
        self.lockin = machines.SR850(8,27.2,1.0)
        self.Ts = []
        self.reVs = []
        self.imVs = []
        self.Vr = []
        self.Rs = []
        self.time = []
        self.recur_id = None

        self.plot_make()

        
        
        
    def _V_to_R(self,Vr,Vs):
        '''
        Convert a voltage measurement into a resistance
        args:
            Vr -- float Voltage reference resistor from multimeter
            Vs -- float Voltage sample, from lock-in
        '''
        return Vs/self.amplification*self.Rr/Vr
    
    def _add_data(self,Ts,Vs,Vr):
        timediff = (datetime.datetime.now()-self.start).total_seconds()
        self.time.append(float(timediff))
        self.Ts.append(Ts)
        self.imVs.append(np.imag(Vs))
        self.reVs.append(np.real(Vs))
        self.Vr.append(Vr)
        self.Rs.append(self._V_to_R(Vr,abs(Vs)))
    
    
    def write_header(self):
        
        with open(self.fnm,'w') as tofile:
            self.start = datetime.datetime.now()
            tofile.write('UBC Resistivity Measurement:')
            tofile.write(str(self.start))
            tofile.write('\n')
            tofile.write('==========================================================================\n')
            tofile.write('Sample Name: {:s}\n'.format(self.sample))
            tofile.write('User: {:s}\n'.format(self.user))
            tofile.write('Material: {:s}\n'.format(self.material))
            tofile.write('==========================================================================\n')
            tofile.write('  Time(s)  |   Temp(K)   |  Vref(V)  |  ReVs (mV)  |  ImVs (mV)  |  Res(Ohm)  \n')
            tofile.write('==========================================================================\n')
            
            
        tofile.close()
    
    def write_dataline(self,index):
        v = index
        with open(self.fnm,'a') as tofile:
            line = '  {:0.05f}  |  {:0.05f}  |  {:0.05f}  |   {:0.05f}   |   {:0.05f}    |  {:0.05f}  \n'.format(self.time[v],self.Ts[v],self.Vr[v],self.reVs[v]*1000,self.imVs[v]*1000,self.Rs[v])
            tofile.write(line)
        tofile.close()
                
            
        
    



    def _build_fig(self):
        fig1 = Figure(figsize=(6,7))
        ax1 = fig1.add_subplot(311)
        ax2 = fig1.add_subplot(312)
        ax3 = fig1.add_subplot(313)
        
        return fig1,ax1,ax2,ax3

    def update_figure(self,fig,axes):
        self.lines = []
        plottables = [self.Ts,self.Rs,self.Vr]
        cols = ['red','blue','black']
        for ai in list(enumerate(axes)):
            ai[1].cla()
            tmp, = ai[1].plot(self.time,plottables[ai[0]],c=cols[ai[0]])
            if len(self.time)>=2:
                ai[1].set_xlim(self.time[0],self.time[-1])

            self.lines.append(tmp)

        fig.canvas.draw()
            
            
        
        


    def plot_make(self):
        self.root = Tk.Tk()
        self.root.configure(background='white')
        self.root.wm_title('UBC Resistivity Measurement')
        fig1,ax1,ax2,ax3 = self._build_fig()
        plt_win = FigureCanvasTkAgg(fig1,master=self.root)
        
      #  plt_win.show()
        
        plt_win.get_tk_widget().grid(row=1,column=4,columnspan=6,rowspan=6)
        
        Tk.Label(master=self.root,text='Setpoint (K):',background='white').grid(row=2,column=0)
        Tbox = Tk.Entry(master=self.root)
        Tbox.insert('end','{:0.03f}'.format(4.2))
        Tbox.grid(row=2,column=1)

        Tk.Label(master=self.root,text='Logging Interval (s):',background='white').grid(row=3,column=0)
        Ibox = Tk.Entry(master=self.root)
        Ibox.insert('end','{:d}'.format(5))
        Ibox.grid(row=3,column=1)

        Tk.Label(master=self.root,text='Direction',background='white').grid(row=4,column=0)        

        HC_opt = Tk.IntVar()
        HC_opt = 0

        Tk.Radiobutton(master=self.root,text='Cool',variable=HC_opt,value=-1,background='white').grid(row=4,column=1)
        Tk.Radiobutton(master=self.root,text='Heat',variable=HC_opt,value=1,background='white').grid(row=4,column=2)

        def _run():
            self.running = True
            self.root.after(1000*int(Ibox.get()),task)
            run_button['state']='disabled'
            stop_button['state']='normal'

        def _stop():
            self.running = False
            self.root.after_cancel(self.recur_id)
            self.recur_id = None
            stop_button['state']='disabled'
            run_button['state']='normal'
            
            
        def _quit():
            self.lakeshore._disconnect()
            self.voltmeter._disconnect()
            self.lockin._disconnect()
            print('Devices Disconnected. Now exiting.')
            self.root.quit()
            self.root.destroy()

        def _save():
            self.fnm =  filedialog.asksaveasfilename(initialdir = "/",title = "Select file",filetypes = (("text files","*.txt"),("all files","*.*")))
            
            if self.fnm[-4:]!='.txt':
                self.fnm = self.fnm+'.txt'
                
            self.write_header()
            
        run_button = Tk.Button(master=self.root,text='START',command=_run)
        run_button.grid(row=5,column=0)
        
        stop_button = Tk.Button(master=self.root,text='STOP',state="disabled",command=_stop)
        stop_button.grid(row=6,column=0)
        
        sv_button = Tk.Button(master=self.root,text='SAVE',command=_save)
        sv_button.grid(row=5,column=1)
        
        qt_button = Tk.Button(master=self.root,text='QUIT',command=_quit)
        qt_button.grid(row=5,column=2)     
        
        Tk.Label(master=self.root,text='Temperature (K):',background='white',fg='red').grid(row=7,column=0)      
        Tk.Label(master=self.root,text='Sample Resistance (Ohm):',background='white',fg='blue').grid(row=7,column=1)
        Tk.Label(master=self.root,text='Reference Voltage (V):',background='white',fg='black').grid(row=7,column=2)    
        Tk.Label(master=self.root,text='Time (s)',background='white').grid(row=7,column=7)
        
        
        def task():
            T = self.lakeshore._measure_T()
            Vr = self.voltmeter._do_acv_measure()
            Vs_x,Vs_y = self.lockin._measure_V()
            Vs = Vs_x + 1.0j*Vs_y
            self._add_data(T,Vs,Vr)
            self.write_dataline(-1)
            self.update_figure(fig1,(ax1,ax2,ax3))
            self.recur_id = self.root.after(int(1000*float(Ibox.get())),task)
           
        
        Tk.mainloop()
        
        
        
if __name__ == "__main__":
    
    

    ni = interface()
        
        
        
            
            
        

        
                    

        





