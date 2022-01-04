# -*- coding: utf-8 -*-
"""
Created on Mon Sep 20 03:41:45 2021

@author: Asterisk
"""

import regex
from pathlib import Path
from common.monsterEnum import loadEntities

import os
from pathlib import Path
if "__file__" in locals():
    currentFile = Path(os.path.realpath(__file__)).parent
else:
    currentFile = Path(".")
    
class MonsterActions():
    def __init__(self,monId,monPath,actionDict,nameDict):
        self.actionDict = actionDict
        self.nameDict = nameDict

def parseActionFile(filePath):
    pattern = r".*Group:[0-9]*,ID:([0-9]*),Name:ACTION::([^\s]*)"
    action = regex.compile(pattern)
    actionDict = {}
    nameDict = {}
    with open(filePath,"r") as file:
        for actionEntry in file:
            g = action.match(actionEntry)
            if g:
                id,name = g.groups()
                name = name.lower()
                actionDict[int(id)] = name
                nameDict[name] = int(id)
                #print(id,name)
        return nameDict,actionDict

def loadActionMaps(pathing = Path(currentFile/"ActionDumps")):
    filenamePattern = r".*em([0-9]*).txt"
    monster = regex.compile(filenamePattern)
    monsterDB = {}
    for file in pathing.rglob("*.txt"):
        g = monster.match(str(file))
        if g:
            monId = int(g.groups()[0])
            nameDict,actionDict = parseActionFile(file)
            monsterDB[monId] = nameDict,actionDict
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

def loadTHKMaps(mappingFile = currentFile/"thkIndices.txt"):
    pattern = r"\s*([0-9]+)\s*([^\s]+)"
    thkMapping = regex.compile(pattern)
    thkMap = {}
    thkUnMap = {}
    with open(mappingFile) as inf:
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