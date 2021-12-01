# -*- coding: utf-8 -*-
"""
Created on Fri Oct 29 12:23:10 2021

@author: Asterisk
"""
from errorHandler import ErrorManaged,copy
    
class Node(ErrorManaged):
    subfields = ["bodylist","header"]
    def __init__(self,header,bodylist):
        self.header = header
        self.bodylist = bodylist
        self.tag = "Node [%s] at line %d"%(self.names()[0],self.header.lineno)
    def indexed(self):
        return self.header.index is not None
    def hasId(self):
        return self.header.id is not None
    def getId(self):
        return self.header.id
    def setId(self,val):
        self.header.id = val
    def getIndex(self):
        return self.header.index
    def setIndex(self,val):
        self.header.index = val
    def names(self):
        return self.header.names
    def renameToScope(self,scope):
        self.header.names = [scope+"::"+n for n in self.header.names]
    def __str__(self):
        result = ""
        result += str(self.header) + "\n"
        result += ''.join((str(b) + '\n' for b in self.bodylist))
        return result
    def resolveScopeToModule(self,modulemap):
        for segment in self.bodylist:
            segment.resolveScopeToModule(modulemap)
    def substituteScopes(self,moduleScopes,actionScopes):
        for segment in self.bodylist:
            segment.substituteScopes(moduleScopes,actionScopes)
    def resolveLocal(self,symbolsTable):
        for segment in self.bodylist:
            segment.resolveLocal(symbolsTable)    
    def resolveInlines(self,controller,scopes):
        for segment in self.bodylist:
            inlineCall = segment.inlineCall()
            if inlineCall:
                scope,target = inlineCall
                if not controller.hasInlineCall(inlineCall):
                    controller.importInline(scopes[scope],target)
    def inlinedCallerCallScopeResolution(self,namespaces):
        for segment in self.bodylist:
            segment.inlinedCallerCallScopeResolution(namespaces)
    def copy(self):
        header = copy(self.header)
        bodylist = [copy(segment) for segment in self.bodylist]
        return Node(header,bodylist)
    def chainedCopy(self,chainMembers):
        copies = []
        for segment in self.bodylist:
            if segment.internalCall():
                node = segment.callTarget()
                if node not in chainMembers:
                    chainMembers.add(node)
                    copies += node.chainedCopy(chainMembers)
        copies.append(copy(self))
        return copies
    def resolveCaller(self,namespace,assignments):
        for segment in self.bodylist:
            segment.resolveCaller(namespace,assignments)
    def resolveTerminals(self,nodeNames,assignments):
        for segment in self.bodylist:
            segment.resolveTerminals(nodeNames,assignments)
    def resolveCalls(self):
        for segment in self.bodylist:
            segment.resolveCalls()
    def resolveActions(self,actionScopes):
        for segment in self.bodylist:
            segment.resolveActions(actionScopes)
    def collectRegisters(self):
        registers = set()
        for segment in self.bodylist:
            registers = registers.union(segment.collectRegisters())
        return registers
    def resolveRegisters(self,namespace):
        for segment in self.bodylist:
            segment.resolveRegisters(namespace)
    def resolveFunctions(self,functionResolver):
        for segment in self.bodylist:
            segment.resolveFunctions(functionResolver)
    def compileProperties(self):
        print("Node",self.getId())
        segmentList = []
        for ix,segment in enumerate(self.bodylist):
            print("Segment",ix)
            segment.parent = self
            dataSegment = segment.compileProperties()
            if dataSegment: segmentList.append(dataSegment)
        self.binaryStructure = {"offset":0,"count":len(segmentList),"id":self.getId(),
                                "segments":segmentList}
        return self.binaryStructure
class NodeHeader(ErrorManaged):
    subfields = []
    def __init__(self,aliaslist,index,lineno):
        self.names = [str(alias) for alias in aliaslist]
        self.id,self.index  = index
        self.lineno = lineno
        self.tag = "Node Header [%s]"%self.names[0]
    def __str__(self):
        return "def " + ' & '.join(map(str,self.names)) + ":"
    def copy(self):
        return NodeHeader(self.names,(self.id,self.index),self.lineno)
