# -*- coding: utf-8 -*-
"""
Created on Tue Oct 12 03:29:04 2021

@author: Asterisk
"""

import regex
from dataclasses import dataclass

abbreviate = lambda x : ''.join([c for c in x if c.isupper()])

class StageData():
    def __init__(self,index,name):
        self.index = int(index)
        self.name = name
        self.abbreviation = abbreviate(name)
    def getId(self):
        return self.index

stageTuple = regex.compile("(\d+),(.*)")

class StageManager(dict):
    def __init__(self):
        self.byID = {}
        self.byName = {}
        self.byAbbreviation = {}
    def append(self,entity):
        self.byID[entity.index] = entity
        self.byName[entity.name] = entity
        self.byAbbreviation[abbreviate(entity.name)] = entity
    def __contains__(self,key):
        return key in self.byID or key in self.byName
    def __getitem__(self,key):
        if key in self.byID: return self.byID[key]
        if key in self.byName: return self.byName[key]
        if key in self.byAbbreviation: return self.byAbbreviation[key]
        raise KeyError
    def getName(self,key):
        return self.byID[key].name
    def scope(self):
        return "st"
    
def loadStages():
    st_enum = StageManager()
    with open("st_enum.csv") as inf:
        for entry in inf:
            groups = stageTuple.match(entry)
            if groups:
                data = StageData(*groups.groups())
                st_enum.append(data)
    return st_enum