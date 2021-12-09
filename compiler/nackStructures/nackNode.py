# -*- coding: utf-8 -*-
"""
Created on Fri Oct 29 12:23:10 2021

@author: Asterisk
"""
from compiler.errorHandler import ErrorManaged, copy


class Node(ErrorManaged):
    subfields = ["segments", "header"]

    def __init__(self, header, segments):
        self.header = header
        self.segments = segments
        self.tag = "Node [%s] at line %d" % (
            self.names()[0], self.header.lineno)

    def indexed(self):
        return self.header.index is not None

    def hasId(self):
        return self.header.id is not None

    def getId(self):
        return self.header.id

    def setId(self, val):
        self.header.id = val

    def getIndex(self):
        return self.header.index

    def setIndex(self, val):
        self.header.index = val

    def names(self):
        return self.header.names

    def renameToScope(self, scope):
        self.header.names = [scope+"::"+n for n in self.header.names]

    def __repr__(self):
        result = ""
        result += repr(self.header) + "\n"
        result += ''.join((repr(b) + '\n' for b in self.segments))
        return result

    def resolveScopeToModule(self, modulemap):
        for segment in self.segments:
            segment.resolveScopeToModule(modulemap)

    def substituteScopes(self, moduleScopes, actionScopes):
        for segment in self.segments:
            segment.substituteScopes(moduleScopes, actionScopes)

    def resolveLocal(self, symbolsTable):
        for segment in self.segments:
            segment.resolveLocal(symbolsTable)

    def resolveInlines(self, controller, symbolsTable):
        for segment in self.segments:
            inlineCall = segment.inlineCall()
            if inlineCall:
                scope, target = inlineCall
                if not controller.hasInlineCall(scope, target.target):
                    controller.importInline(target.module, scope, target)
                recipient = controller.retrieveInlineCall(scope, target.target)
                segment.reconnectChain(recipient)

    def copy(self):
        header = copy(self.header)
        segments = [copy(segment) for segment in self.segments]
        return Node(header, segments)

    def chainedCopy(self, chainMembers):
        copies = []
        copied = copy(self)
        chainMembers[self] = copied
        for segment, nsegment in zip(self.segments, copied.segments):
            if segment.internalCall():
                node = segment.callTarget()
                if node not in chainMembers:
                    copies += node.chainedCopy(chainMembers)
                nsegment.reconnectChain(chainMembers[node])
        copies.append(copied)
        return copies

    def resolveCaller(self, namespace, assignments):
        for segment in self.segments:
            segment.resolveCaller(namespace, assignments)

    def resolveTerminal(self, symbolsTable):
        for segment in self.segments:
            segment.resolveTerminal(symbolsTable)

    def resolveCalls(self):
        for segment in self.segments:
            segment.resolveCalls()

    def resolveActions(self, actionScopes):
        for segment in self.segments:
            segment.resolveActions(actionScopes)

    def collectRegisters(self):
        registers = set()
        for segment in self.segments:
            registers = registers.union(segment.collectRegisters())
        return registers

    def resolveRegisters(self, namespace):
        for segment in self.segments:
            segment.resolveRegisters(namespace)

    def resolveFunctions(self, functionResolver):
        for segment in self.segments:
            segment.resolveFunctions(functionResolver)

    def compileProperties(self):
        # print("Node",self.getId())
        segmentList = []
        for ix, segment in enumerate(self.segments):
            # print("Segment",ix)
            segment.parent = self
            dataSegment = segment.compileProperties()
            if dataSegment:
                segmentList.append(dataSegment)
        self.binaryStructure = {"offset": 0, "count": len(segmentList), "id": self.getId(),
                                "segments": segmentList}
        return self.binaryStructure


class NodeHeader(ErrorManaged):
    subfields = []

    def __init__(self, aliaslist, index, lineno):
        self.names = [alias for alias in aliaslist]
        self.id, self.index = index
        self.lineno = lineno
        self.tag = "Node Header [%s]" % self.names[0]

    def __repr__(self):
        add = ""
        if self.id is not None: add+=" {%d}"%self.id
        if self.index is not None: add+=" [%d]"%self.index
        return str(self)+add

    def __str__(self):
        return "def " + ' & '.join(map(str, self.names))

    def copy(self):
        return NodeHeader(self.names, (self.id, self.index), self.lineno)
