# -*- coding: utf-8 -*-
"""
Created on Thu Nov 25 04:46:27 2021

@author: Asterisk
"""
from errorHandler import ErrorManaged,copy
import thk

class TypeNub(ErrorManaged):
    def __init__(self,propName,raw_id):
        self.propName = propName
        self.tag = propName
        self.raw_id = raw_id
    def resolveProperties(self,storage):
        storage(self.propName,self.raw_id)
    def copy(self):
        return type(self)(self.propName,self.raw_id)
    def __str__(self):
        return self.propName
    def __repr__(self):
        return str(self)

class Segment(ErrorManaged):
    memberList = ["function","call","directive","action","branchingControl","randomType",
                  "terminator","metaparams","chance"]
    subfields = ["_"+m for m in memberList]
    tag = "Node Segment"
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
    def copy(self):
        s = Segment()
        for f in self.memberList:
            field = "_"+f
            setattr(s,field,copy(getattr(self,field)))
        return s
    def existingCheck(self,check):
        if getattr(self,"_"+check) is not None:
            self.errorHandler.segmentDuplicateProperty()
    def addFunction(self,function):
        self.existingCheck("function")
        self._function = function
    def addAction(self,action):
        self.existingCheck("action")
        self._action = action
    def addCall(self,call):
        self.existingCheck("call")
        self._call = call
    def addDirective(self,directive):
        self.existingCheck("directive")
        self._directive = directive
    def startConditional(self):
        self.existingCheck("branchingControl")
        self._branchingControl = TypeNub("branchingControl",0x2)
    def addConditionalBranch(self):
        self.existingCheck("branchingControl")
        self._branchingControl = TypeNub("branchingControl",0x4)
    def endConditional(self):
        self.existingCheck("branchingControl")
        self._branchingControl = TypeNub("branchingControl",0x8)
    def addEndNode(self):
        self.existingCheck("randomType")
        self._randomType = TypeNub("endRandom",0x1)
        self._terminator = TypeNub("nodeEndingData",10000)
    def addChance(self,chance):
        self.existingCheck("chance")
        self._chance = chance
    def endChance(self):
        self.existingCheck("branchingControl")
        self._branchingControl = TypeNub("branchingControl",0x1)
    def addConclude(self):
        self.existingCheck("branchingControl")
        self._branchingControl = TypeNub("branchingControl",0x10)
    def addMeta(self,params):
        self._metaparams = params
    def getNodeId(self):
        return self.parent.getId()
    def substituteScopes(self,moduleScopes,actionScopes):
        for member in ["call","action"]:
            value = getattr(self,"_"+member)
            if value is not None:
                value.substituteScope(moduleScopes,actionScopes)
    def resolveScopeToModule(self,modulelist):
        if self._call is not None:
            self._call.resolveScopeToModule(modulelist)
    def resolveLocal(self,symbolsTable):
        for elementName in ["function","call","action","chance"]:
            #Functions, Actions and Chance are given full resolution
            #Calls only resolve to a reference of the object not to a
            #proper value
            element = getattr(self,"_"+elementName)
            if element is not None:
                element.resolveLocal(symbolsTable)
        #self._resolutionOperator(symbolsTable.nodeIndices,symbolsTable.nodes,
        #                         symbolsTable.vars,"localResolve","resolveImmediateId")
    def _resolutionOperator(self,localIndices,localNames,variableNames,
                                callResolution,fieldResolution):
        if callResolution:
            if self._call is not None:
                getattr(self._call,callResolution)(localIndices,localNames)
        if fieldResolution:
            for field in ["function","action","chance"]:
                fieldVal = getattr(self,"_"+field)
                if fieldVal is not None:
                    getattr(fieldVal,fieldResolution)(variableNames)
            if self._chance:
                getattr(self._chance,fieldResolution)(variableNames)
    def inlinedCallerCallScopeResolution(self,namespace):        
        self._resolutionOperator({},namespace,{},"inlinedCallerCallScopeResolution","")
    def __str__(self):
        return ','.join([attr
            for attr in ["function","call","action","directive","branchingControl",
                         "randomType","terminator","metaparams"]
            if getattr(self,"_"+attr) is not None])
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
    def resolveCaller(self,nodeNames,variableNames):
        self._resolutionOperator({},nodeNames,variableNames,
                                     "resolveCaller","resolveCallerId")
    def resolveTerminals(self,nodeNames,variableNames):
        self._resolutionOperator({},nodeNames,variableNames,
                                     "resolveTerminals","resolveTerminalId")
    def resolveCalls(self):
        if self._call:
            return self._call.resolveCalls()
    def resolveActions(self,actionScopes):
        if self._action:
            self._action.resolveAction(actionScopes)
    def collectRegisters(self):
        if self._function and self._function.typing == "register": #else function
            return self._function.collectRegisters()
        else:
            return []
    def resolveRegisters(self,namespace):
        if self._function and self._function.typing == "register": #else function
            return self._function.resolveName(namespace)
    def resolveFunctions(self,functionResolver):
        if self._function:
            self._function.resolveFunctions(functionResolver)
    def compileProperties(self):
        dataSegment = {}
        def testAdd(propertyName,propertyValue):
            if propertyName in dataSegment:
                self.errorHandler.repeatedProperty(propertyName)
            dataSegment[propertyName] = propertyValue
        for member in self.memberList:
            var = getattr(self,"_"+member)
            if member == "metaparams":
                pass
            else:
                if var: var.resolveProperties(testAdd)
        for key,val in self._metaparams.items():
            if hasattr(val,"raw_id"): testAdd(key,val)
            else: val.erroHandler.unresolvedIdentifier()
        if "nodeEndingData" in dataSegment:
            dataSegment["nodeEndingData"] += self.parent.getId()
        if "functionID" not in dataSegment: 
            default = 0 if "endChance" in dataSegment else 2
            dataSegment["functionID"] = default
        for field in thk._Segment.subcons:
            name = field.name
            if name not in dataSegment:
                dataSegment[name] = 0
            if name == "padding":
                dataSegment["padding"] = [0]*12
        return dataSegment