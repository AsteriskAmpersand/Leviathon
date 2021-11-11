# -*- coding: utf-8 -*-
"""
Created on Tue Oct 12 03:03:27 2021

@author: Asterisk
"""
from fexParse import buildParser
from stageEnum import loadStages
from monsterEnum import loadEntities
import keywords as key

import struct
from collections import defaultdict

st_enum = loadStages()
em_enum = loadEntities()

def enumCheck(enum,field):
    def check(segment):
        val = getattr(segment,field)
        if val not in enum:
            return str(val)
        else:
            return enum.scope() + "." + enum.getName(val)
    return check

def floatCast(field):
    def cast(segment):
        val = getattr(segment,field)
        return struct.unpack('f',struct.pack('<L', val))
    return cast

def segmentGet(field):
    def get(segment):
        return getattr(segment,field)
    return get

class ParametrizationError(Exception):
    pass

def eq(x,y):
    return x == y

class ForkEntry():
    def __init__(self,condition,target):
        self.accessorCond = []
        self.accessorCons = []
        self.fallthrough = False
        self.conditionCheck = self.functionalizeConditions(condition)
        self.target = target
        self.consequenceGenerate = self.functionalizeTarget(target)
        #inversibility conditions for compilation
        self.verify()

    def condition(self,segment):
        return self.conditionCheck(segment)
    def consequence(self,segment):
        for v in self.accessorCond+self.accessorCons:
            segment.log(v)
        return self.consequenceGenerate(segment)

    def functionalizeConditions(self,conditions):
        if not conditions:
            self.fallthrough = True
        for cond in conditions:
                field = cond.accessor.field
                if field in self.accessorCond:
                    raise ParametrizationError("Accessor used multiple times in condition")
                self.accessorCond.append(field)
        def acceptSegment(x):
            for cond in conditions:
                field = cond.accessor.field
                op = {"==": eq}[cond.comparison]
                target = cond.numeric
                if not op(getattr(x,field),target):
                    return False
            return True
        return acceptSegment
    
    def parseField(self,field,dataType,dataIndex,mappings):
        if dataType is None:
             mappings.append(segmentGet(field))
             return "%d"
        else:
            if dataType == "CAST":
                mappings.append(floatCast(field))
                return "%f"
            elif dataType == "ENUM":
                if dataIndex == "st_enum":
                    enum = st_enum
                elif dataIndex == "em_enum":
                    enum = em_enum
                mappings.append(enumCheck(enum,field))
                return "%s"
    
    def functionalizeTarget(self,consequence):
        c = consequence
        if type(consequence) is str:
            return lambda x: consequence
        else:
            formatString = ""
            mappings = []
            fieldSets,dataTypesSets,dataIndicesSets,cumulatives,term = c.functionalStructure()
            for fields,dataTypes,dataIndices,strCumul in zip(fieldSets,dataTypesSets,dataIndicesSets,cumulatives):
                for field in fields:
                    if field in self.accessorCons:
                        raise ParametrizationError("Accessor used multiple times in target")
                    self.accessorCons.append(field)
                formatString += strCumul
                formatString += "("
                formatString += ','.join([self.parseField(field,dtt,dti,mappings) for field,dtt,dti in zip(fields,dataTypes,dataIndices)])
                formatString += ")"
            formatString += term
            def stringFunction(segment):
                return formatString%tuple(f(segment) for f in mappings) 
            return stringFunction
    def verify(self):
        for ele in self.accessorCond:
            if ele in self.accessorCons:
                raise ParametrizationError("Accessor used in both condition and target")
        return
    
def defaultResolution(segment):
    base = key.FUNCTION + "#%X(%s)"
    segment.log("functionType")
    parameters = ""
    if segment.parameter1:
        parameters = str(segment.parameter1)
        segment.log("parameter1")
    if segment.parameter2:
        if not segment.parameter1: segment.log("parameter1")
        segment.log("parameter2")
        parameters = "%d,%d"%(segment.parameter1,segment.parameter2)
    return base%(segment.functionType,parameters)

class ForkResolve():
    def __init__(self,index,tupleDict):
        self.index = index
        self.fallthrough = False
        forkedEntries = []
        for conditions,consequence in tupleDict.items():
            fe = ForkEntry(conditions,consequence)
            forkedEntries.append(fe)
            if fe.fallthrough: self.fallthrough = True
        self.entries = forkedEntries
                
    def resolve(self,segment):
        for fork in self.entries:
            if fork.condition(segment):
                segment.log("functionType")
                return "self." + fork.consequence(segment)
        #Parameter logging inclusion and the tracker
        return defaultResolution(segment)
        
    def merge(self,other):
        ltail, rtail = self.getTail(), other.getTail()
        tail = ltail if rtail is None else rtail
        self.fallthrough = ltail is not None or rtail is not None
        newForks = other.getTailess()
        oldForks = self.getTailess()
        fallthroughFork = [tail] if tail else []   
        self.entries = newForks + oldForks + fallthroughFork
        return self
    
    def getTail(self):
        if self.fallthrough:
            return self.entries[-1]
        return None
            
    def getTailess(self):
        if self.fallthrough:
            return self.entries[:-1]
        return self.entries

class CheckCompiler():
    def __init__(self,parserResult):
        compoundReverseMapper = defaultdict(lambda: defaultdict(list))
        for functionID,conditions in parserResult.items():
            for parameters,target in conditions.items():
                functionData = [(param.accessor,param.numeric) for param in parameters]
                functionData.append(("functionID",functionID))
                compoundReverseMapper[target.signature()][target.literalSignature()].append((target,functionData))
        self.compoundReverseMapper = compoundReverseMapper        
    def resolve(self,functionData,storage):
        sig = functionData.signature()
        if sig not in self.compoundReverseMapper: raise KeyError("Missing Signature")
        subChoices = self.compoundReverseMapper[sig]
        subsig = functionData.literalSignature()
        if subsig not in subChoices: raise KeyError("Missing Literal Signatures")
        targets = subChoices[subsig]
        for t,functionInfo in targets:
            if t.exactMatch(functionData):
                for varName,varVal in functionInfo:
                    storage(varName,varVal)
                for varName,varVal in t.parse(functionData):
                    storage(varName,varVal)
                return
        raise KeyError("Missing Exact Match")
    
class CheckResolver():
    def __init__(self,parserResult):
        self.functionTable = {}
        for key,val in parserResult.items():
            try:
                self.functionTable[key] = ForkResolve(key,val)
            except ParametrizationError as e:
                print("Error Generating Parametrization %X"%key)
                print(e)
    def resolve(self,segment):
        if segment.functionType in self.functionTable:
            return self.functionTable[segment.functionType].resolve(segment)
        else:
            return defaultResolution(segment)
    def registerResolve(self,segment,registerName):
        segment.log("functionType")
        segment.log("parameter1")
        if 0x80 <= segment.functionType <= 0x93:
            op = "|-" if segment.parameter1 else "++"
        else:
            op = "%s %d"%(["==","<=" ,"<" ,">=" ,">" ,"!="][segment.parameter1],segment.parameter2)
            segment.log("parameter2")
        return "[%s %s]"%(registerName,op)
    def merge(self,other):
        self.functionTable.update(other.functionTable)
        for key in other.keys():
            if key not in self.functionTable:
                self.functionTable[key] = other.functionTable[key]
            else:
                self.functionTable[key].merge(other.functionTable[key])
        return self
    def keys(self):
        return self.functionTable.keys()

def buildCompiler(path = None):
    if path is None: path = "default.fexty"
    return CheckCompiler(buildParser(path))

def buildResolver(path = None):
    if path is None: path = "default.fexty"
    return CheckResolver(buildParser(path))

if __name__ in "__main__":
    resolver = buildResolver("default.fexty")