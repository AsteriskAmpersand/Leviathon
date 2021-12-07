# -*- coding: utf-8 -*-
"""
Created on Thu Nov 25 04:46:27 2021

@author: Asterisk
"""
from compiler.errorHandler import ErrorManaged, copy
import common.thk as thk


class TypeNub(ErrorManaged):
    def __init__(self, propName, raw_id):
        self.propName = propName
        self.tag = propName
        self.raw_id = raw_id

    def resolveProperties(self, storage):
        storage(self.propName, self.raw_id)

    def copy(self):
        return type(self)(self.propName, self.raw_id)

    def __str__(self):
        return self.propName

    def __repr__(self):
        return "<%s [%d]>"%(str(self),self.raw_id)


class SegmentInit():

    def __init__(self):
        self._function = None
        self._call = None
        self._directive = None
        self._action = None
        self._branchingControl = None
        self._randomType = None
        self._terminator = None
        self._metaparams = {}
        self._chance = None

    def existingCheck(self, check):
        if getattr(self, "_"+check) is not None:
            self.errorHandler.segmentDuplicateProperty()

    def addFunction(self, function):
        self.existingCheck("function")
        self._function = function

    def addAction(self, action):
        self.existingCheck("action")
        self._action = action

    def addCall(self, call):
        self.existingCheck("call")
        self._call = call

    def addDirective(self, directive):
        self.existingCheck("directive")
        self._directive = directive

    def startConditional(self):
        self.existingCheck("branchingControl")
        self._branchingControl = TypeNub("branchingControl", 0x2)

    def addConditionalBranch(self):
        self.existingCheck("branchingControl")
        self._branchingControl = TypeNub("branchingControl", 0x4)

    def endConditional(self):
        self.existingCheck("branchingControl")
        self._branchingControl = TypeNub("branchingControl", 0x8)

    def addEndNode(self):
        self.existingCheck("randomType")
        self._randomType = TypeNub("endRandom", 0x1)
        self._terminator = TypeNub("nodeEndingData", 10000)

    def addChance(self, chance):
        self.existingCheck("chance")
        self._chance = chance

    def endChance(self):
        self.existingCheck("branchingControl")
        self._branchingControl = TypeNub("branchingControl", 0x1)

    def addConclude(self):
        self.existingCheck("branchingControl")
        self._branchingControl = TypeNub("branchingControl", 0x10)

    def addMeta(self, params):
        self._metaparams = params


class SegmentFinalResolution():

    def resolveCalls(self):
        if self._call:
            return self._call.resolveCalls()

    def resolveActions(self, actionScopes):
        if self._action:
            self._action.resolveAction(actionScopes)

    def collectRegisters(self):
        if self._function and self._function.typing == "register":  # else function
            return self._function.collectRegisters()
        else:
            return []

    def resolveRegisters(self, namespace):
        if self._function and self._function.typing == "register":  # else function
            return self._function.resolveName(namespace)

    def resolveFunctions(self, functionResolver):
        if self._function and self._function.typing != "register":
            self._function.resolveFunctions(functionResolver)

    def defaultValues(self,field):
        if field in {"extRefThkID", "extRefNodeID", "localRefNodeID"}:
            return -1
        else:
            return 0

    def compileProperties(self):
        dataSegment = {}
        def testAdd(propertyName, propertyValue):
            if type(propertyValue) is not int:
                self.errorHandler.resolutionError(propertyName)
            if propertyName in dataSegment:
                self.errorHandler.repeatedProperty(propertyName)
            dataSegment[propertyName] = propertyValue
        for member in self.memberList:
            var = getattr(self, "_"+member)
            if member == "metaparams":
                pass
            else:
                if var:
                    var.resolveProperties(testAdd)
        for key, val in self._metaparams.items():
            if val.raw_id is not None:
                testAdd(key, val.getRaw())
            else:
                val.erroHandler.unresolvedIdentifier()
        if "nodeEndingData" in dataSegment:
            dataSegment["nodeEndingData"] += self.parent.getId()
        if "functionType" not in dataSegment:
            default = 0 if "endChance" in dataSegment else 2
            dataSegment["functionType"] = default
        for field in thk.Segment.subcons:
            name = field.name
            if name not in dataSegment:
                dataSegment[name] = self.defaultValues(name)
            if name == "padding":
                dataSegment["padding"] = [0]*12
        return dataSegment
    

def resolutionOp(resolveCall = True):
    def resolutionOpF(function):
        def func(self,*args,**kwargs):
            for elementName in ["function", "action", "chance"] + (["call"] if resolveCall else []):
                # Functions, Actions and Chance are given full resolution
                # Calls only resolve to a reference of the object not to a
                # proper value
                element = getattr(self, "_"+elementName)
                if element is not None:
                    getattr(element,function.__name__)(*args,**kwargs)
            function(self,*args,**kwargs)
        return func
    return resolutionOpF


class Segment(SegmentInit, SegmentFinalResolution, ErrorManaged):
    memberList = ["function", "call", "directive", "action", "branchingControl", "randomType",
                  "terminator", "metaparams", "chance"]
    subfields = ["_"+m for m in memberList]
    tag = "Node Segment"

    def copy(self):
        s = Segment()
        for f in self.memberList:
            field = "_"+f
            setattr(s, field, copy(getattr(self, field)))
        return s

    def getNodeId(self):
        return self.parent.getId()
    
    @resolutionOp()
    def resolveLocal(self, symbolsTable): pass
    
    @resolutionOp(resolveCall = False)
    def resolveCaller(self, namespaces, var):
        if self._call is not None:
            self._call = self._call.resolveCaller(namespaces,var)
            self.inheritChildren(self._call)

    @resolutionOp(resolveCall = False)
    def resolveTerminal(self, symbolsTable): 
        if self._call is not None:
            self._call = self._call.resolveTerminal(symbolsTable)
            self.inheritChildren(self._call)

    def reconnectChain(self,node_target):
        self._call = self._call.reconnectChain(node_target)
        self.inheritChildren(self._call)

    def internalCall(self):
        if self._call:
            return self._call.internalCall()
        return False

    def inlineCall(self):
        if self._call:
            return self._call.inlineCall()
        return False

    def callTarget(self):
        if self._call:
            return self._call.node_target
        self.errorHandler.missingCallTarget()

    def __repr__(self):
        return ' '.join([repr(getattr(self,"_"+m)) for m in self.memberList
                         if getattr(self,"_"+m) is not None])
                

