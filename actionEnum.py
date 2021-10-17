# -*- coding: utf-8 -*-
"""
Created on Mon Sep 20 03:41:45 2021

@author: Asterisk
"""

import regex
from pathlib import Path
from monsterEnum import loadEntities

class MonsterActions():
    def __init__(self,monId,monPath,actionDict,nameDict):
        self.actionDict = actionDict
        self.nameDict = nameDict

def loadActionMaps():
    filenamePattern = r".*em([0-9]*)_([0-9]*).txt"
    pattern = r".*Group:[0-9]* ID:([0-9]*) Name:ACTION::([^\s]*)"
    action = regex.compile(pattern)
    monster = regex.compile(filenamePattern)
    monsterDB = {}
    for file in Path("./ActionDumps").rglob("*.txt"):
        g = monster.match(str(file))
        if g:
            monId,monSpecies = map(int,g.groups())
            actionDict = {}
            nameDict = {}
            for actionEntry in file.open():
                g = action.match(actionEntry)
                if g:
                    id,name = g.groups()
                    name = name.lower()
                    actionDict[int(id)] = name
                    nameDict[name] = int(id)
                    #print(id,name)
            monsterDB[(monId,monSpecies)] = nameDict,actionDict
    return monsterDB

class THKContextResolver():
    def __init__(self,preloads = None):
        if preloads is None:
            preloads = loadTHKMaps()
        self.thkToModule, self.moduleToThk  = preloads
    def resolve(self,key):
        if key in self.thkToModule:
            return self.thkToModule[key]
        else:
            return "THK_%02d"%key

def loadTHKMaps():
    pattern = r"\s*([0-9]+)\s*([^\s]+)"
    thkMapping = regex.compile(pattern)
    thkMap = {}
    thkUnMap = {}
    with open("thkIndices.txt") as inf:
        for line in inf:
            match = thkMapping.match(line)
            if match:
                ix,name = match.groups()
                ix = int(ix)
                thkMap[ix] = name
                thkUnMap[name] = ix
    return THKContextResolver((thkMap,thkUnMap))

def untype(subtype):
    t = subtype.replace("em00","").replace("em0","").replace("em","")
    try:
        return int(t)
    except:
        return -1

def monsterDataCheck(pandasDB):
    am = loadActionMaps()
    def lookup(entry):
        if (untype(entry.subtype), entry.subspecies) in am:
            if entry.actionID in am[(untype(entry.subtype), entry.subspecies)][1]:
                return am[(untype(entry.subtype), entry.subspecies)][1][entry.actionID]
        return "UNKN"
    pandasDB["actionName"] = pandasDB.apply(lookup,axis = 1)

class DefaultDataEnum():
    def __init__(self):
        self.actionMap = loadActionMaps()
        self.thkModuleData = {}
        resolver = loadTHKMaps()
        thkToModule, moduleToThk = resolver.thkToModule, resolver.moduleToThk
        self.thkModuleData["em"] = (thkToModule, moduleToThk)
        self.entityMap = loadEntities(self.actionMap)
    def moduleInfo(self,typing):
        if typing in self.thkModuleData:
            return self.thkModuleData['em'][0]
        else:
            return {}