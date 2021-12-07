# -*- coding: utf-8 -*-
"""
Created on Tue Dec  7 06:15:31 2021

@author: Asterisk
"""

from common.thk import Segment
from common import keywords as key
from common import thklSpecStr as thklSpec

def checkEmptyFields(node):
    segment = node.segments[0]
    for field in Segment.subcons:
        name = field.name
        if name in ["padding","monsterID","isPalico","log"]:
            continue
        val = getattr(segment,name)
        if name in ["extRefThkID","extRefNodeID","localRefNodeID"]:
            if val != -1:
                #print("REF")
                return False
        elif name in ["endRandom"]:
            if val not in [0,1]:
                #print("ENDRANDOM")
                return False
        elif name in ["nodeEndingData"]:
            if val // 10000 not in [0,1]:
                #print("ENDIGNDATA")
                return False
        else:
            if val != 0:
                print(name)
                return False
    return True

def checkEmptyNode(node):
    if node.id == 0:
        if len(node.segments) == 1:
            if checkEmptyFields(node):
                return False
    return True

class NodeListing():
    def __init__(self):
        self.idToNode = {}
        self.indexToNode = {}
        self.rawIndexToNode = {}
        self.nodeToIndex = {}
        self.nodeToId = {}
    def conditionalAdd(self,dic,key,val):
        if key in dic and key != 0:
            raise KeyError("Existing entry on node manifest: %s (%s <> %s)"%(str(key), val, dic[key].getName()))
        dic[key] = val
    def add(self,node,index):
        self.conditionalAdd(self.idToNode,node.id,node)
        self.conditionalAdd(self.indexToNode,index,node)
        self.conditionalAdd(self.rawIndexToNode,node.index,node)
        for name in node.names:
            self.conditionalAdd(self.nodeToIndex,name,index)
            self.conditionalAdd(self.nodeToId,name,node.id)
    
class MissingCallID(Exception):
    def __init__(self, scope, iD):
        self.scopeIndex = scope
        self.id = iD
       
class CallResolver(dict):
    def __init__(self,premade = None):
        self.localIndex = None
        if premade is not None:
            self.update(premade)
    def setLocal(self,index):
        self.localIndex = index
    @classmethod
    def defaultCall(cls,callIndex):
        return key.CALL + "#%03d"%callIndex
    def resolve(self,segment):
        segment.log("extRefThkID")
        segment.log("extRefNodeID")
        segment.log("localRefNodeID")
        if segment.extRefThkID != -1:
            scope = segment.extRefThkID
            index = segment.extRefNodeID
            if scope in self:
                if index in self[scope].idToNode:
                    return scope,self[scope].idToNode[index].names[0]
                else:
                    raise MissingCallID(scope,index)
            else:
                return scope,self.defaultCall(index)
        elif segment.localRefNodeID != -1:
            scope = self.localIndex
            index = segment.localRefNodeID
            if scope in self:
                if index in self[scope].rawIndexToNode:
                    return "local",self[scope].rawIndexToNode[index].names[0]
                else:
                    raise MissingCallID("local",index)
            else:
                return None,self.defaultCall(index)
        else:
            return None,""


class RegisterScheduler():
    def __init__(self, force=False):
        self.mappings = {}
        self.force = force
    def defaultName(self,registerIndex):
        return "$"+chr(ord("A")+registerIndex)
    def addEntries(self,entries):
        for entry in entries:
            self.entries[entry] = self.defaultName(entry)
    def label(self,index,name):
        self.mappings[index] = name
    def resolve(self,registerIndex):
        if registerIndex in self.mappings and not self.force:
            return self.mappings[registerIndex]
        else:
            return self.defaultName(registerIndex) 
    def declarations(self,keep = False):
        declarations = []
        for entry,name in self.mappings.items():
            letter = self.defaultName(entry)
            if not keep:
                declarations.append(thklSpec.register_anon_str%(name))
            else:
                declarations.append(thklSpec.register_str%(name,letter))
        return '\n'.join(declarations)+"\n\n" if declarations else ""
class ScopeResolver():
    def __init__(self):
        self.importList = set()
        self.scopeMapping = {55:"Global"}
        self.inverseScopeMapping = {"Global":55}
    def addEntry(self,index,name):
        self.scopeMapping[index] = name
        self.inverseScopeMapping[name] = index
    def startContext(self):
        self.importList = set()
    def imports(self):
        return self.importList
    def defaultContext(self,index):
        return "Thk_%02d"%index
    def resolve(self,contextIndex):
        if contextIndex not in self.scopeMapping:
            scopeTarget = self.defaultContext(contextIndex)
            scopeValue = contextIndex
        else:
            scopeTarget = self.scopeMapping[contextIndex]
            scopeValue = scopeTarget
        self.importList.add((scopeValue,scopeTarget))
        return scopeTarget
