# -*- coding: utf-8 -*-
"""
Created on Thu Nov 25 04:45:06 2021

@author: Asterisk
"""
from errorHandler import ErrorManaged,copy

fDirectiveMap = {"return":0x8,"repeat":0x4,"reset":0x80}
bDirectiveMap = {v:k for k,v in fDirectiveMap.items()}
class Directive(ErrorManaged):
    tag = "Directive"
    subfields = []
    def __init__(self,command):
        self.target = command
        self.raw_target = fDirectiveMap[command]
    def copy(self):
        return Directive(bDirectiveMap[self.raw_target])
    def resolveProperties(self,storage):
        storage("flowControl",self.raw_target)
    def __str__(self):
        return "<Dir> " + self.target