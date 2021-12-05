# -*- coding: utf-8 -*-
"""
Created on Tue Nov  9 06:52:03 2021

@author: Asterisk
"""

    
def Autonumber(reserved=set()):
    i = 0
    while True:
        while i in reserved: i+=1
        yield i
        i+=1