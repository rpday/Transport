# -*- coding: utf-8 -*-
"""
Created on Tue Feb  5 16:27:19 2019

@author: ARPES08
"""
import matplotlib.pyplot as plt
import numpy as np

class data_obj:
    
    def __init__(self,fnm):
        
        self.data = self.load_data(fnm)
        
    def __plot_data__(self,x_key,y_key):
        
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot(self.data[x_key],self.data[y_key])
        
        return fig,ax
    
    
    def load_data(self,fnm):
        data = {'time':[],'T':[],'Tr':[],'Vr':[],'Rs':[],'ImV':[],'ReV':[]}
        with open(fnm,'r') as fromf:
            for line in fromf:
                data_line = line.split('|')
                try:
                    tmp_data  = [float(t) for t in data_line]
                except ValueError:
                    continue
                data['time'].append(tmp_data[0])
                data['T'].append(tmp_data[1])
                data['Tr'].append(tmp_data[2])
                data['Vr'].append(tmp_data[3])
                data['ReV'].append(tmp_data[4])
                data['ImV'].append(tmp_data[5])
                data['Rs'].append(tmp_data[6])
        return data    



if __name__ == "__main__":
    data_cool = data_obj('C:/Users/rday/Downloads/Transport-master/Transport-master/FeSe_heat_03_11022019.txt')
    data_cool.__plot_data__('T','Rs')
    
                
