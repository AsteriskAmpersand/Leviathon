# -*- coding: utf-8 -*-
"""
Created on Tue Oct 12 03:27:14 2021

@author: Asterisk
"""
import regex
from dataclasses import dataclass
import keywords as key

@dataclass
class EntityData():
    typing: str
    species: int
    subspecies: int
    name: str
    gameID: int
    actionToName: dict
    nameToAction: dict
    def resolveActionIndex(self,actionIndex):
        if not hasattr(self,"scopeName"):self.scopeName = "monster"
        if actionIndex in self.actionToName:
            return self.scopeName+"."+self.actionToName[actionIndex]
        else:
            return "%s#%02X"%(key.ACTION, actionIndex)
    def getId(self):
        return self.gameID
    
class EntityManager():
    kindmap = {"em":"Monster","ems":"Small Monster","otomo":"Otomo"}
    def __init__(self):
        self.byStringTriplet = {}
        self.byTriplet = {}
        self.byGameID = {}
        self.byName = {}
        self.list = []
    def append(self,entity):
        triplet = (entity.typing,entity.species,entity.subspecies)
        self.byStringTriplet[entity.typing+str(entity.species)+"_"+str(entity.subspecies)]=entity
        self.byTriplet[triplet]=entity
        self.byGameID[entity.gameID]=entity
        self.byName[entity.name]=entity
        self.list.append(entity)
    def __contains__(self,key):
        if key in self.byStringTriplet: return True
        if key in self.byTriplet: return True
        if key in self.byGameID: return True
        if key in self.byName: return True
        if key in self.list: return True
        return False
    def __getitem__(self,key):
        if key in self.byStringTriplet: return self.byStringTriplet[key]
        if key in self.byTriplet: return self.byTriplet[key]
        if key in self.byGameID: return self.byGameID[key]
        if key in self.byName: return self.byName[key]
        raise KeyError
    def actionsByName(self,name):
        return self.byName[name].nameToAction,self.byName[name].actionToName
    def get(self,key,field):
        return getattr(self[key],field)
    def getName(self,key):
        return self.get(key,"name")
    def scope(self):
        return "em"

def loadEntities(actionMapper = {}):
    pattern = ("(ems|em)([0-9]{3})_([0-9]{2}),([^,]*),([0-9]*),([0-9]*),([^\s])")
    nameFormatMapping = regex.compile(pattern)
    entities = EntityManager()
    with open("monIds.txt") as inf:
        for line in inf:
            match = nameFormatMapping.match(line)
            if match:
                monsterKind,monsterID,speciesID,monsterBase,iconID,gameID,monsterName = match.groups()
                monsterID,speciesID,iconID,gameID = map(int,[monsterID,speciesID,iconID,gameID])
                aToN, nToA = {},{}
                if (monsterID,speciesID) in actionMapper:
                    aToN,nToA = actionMapper[(monsterID,speciesID)]
                entity = EntityData(monsterKind,monsterID,speciesID,monsterBase,gameID,nToA,aToN)
                entities.append(entity)
        #entities.append(EntityData("otomo",0,0,"Palico",0,{},{}))
    return entities