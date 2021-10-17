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

stageTuple = regex.compile("(\d+),(.*)")

class StageManager(dict):
    def __init__(self):
        self.idToName = {}
        self.nameToId = {}
        self.abbreviateToId = {}
    def append(self,entity):
        self.idToName[entity.index] = entity.name
        self.nameToId[entity.name] = entity.index
        self.abbreviateToId[abbreviate(entity.name)] = entity.index
    def __contains__(self,key):
        return key in self.idToName or key in self.nameToId
    def __getitem__(self,key):
        if key in self.idToName: return self.idToName[key]
        if key in self.nameToId: return self.nameToId[key]
        if key in self.abbreviateToId: return self.abbreviateToId[key]
        raise KeyError
    def getName(self,key):
        return self.idToName[key]
        
def loadStages():
    st_enum = StageManager()
    with open("st_enum.csv") as inf:
        for entry in inf:
            groups = stageTuple.match(entry)
            if groups:
                data = StageData(*groups.groups())
                st_enum.append(data)
    return st_enum