# -*- coding: utf-8 -*-
"""
Created on Tue Dec  7 06:17:23 2021

@author: Asterisk
"""
from pathlib import Path

from common import keywords as key
from common.thk import Thk
from common.actionEnum import loadActionMaps
from common.monsterEnum import loadEntities
from common.fexLayer import buildResolver
from decompiler.thkDecompileUtils import (CallResolver, RegisterScheduler,
                                          ScopeResolver)
from decompiler.decompilerUtils import Decompiler
from decompiler.nodeDecompiler import NodeDecompiler
from decompiler.thkDecompileUtils import NodeListing, checkEmptyNode


class THKDecompiler(Decompiler):
    # check references on nodes to see if there's any missing index, if there is
    # need to re-enable those function on fixed indices

    # need to build scope resolution operator
    # it needs to log all of the scopes checked on it to add them
    # to the declaration at the top

    #actionResolver = loadActionMaps
    #entityResolver = loadEntities(actionResolver)
    def __init__(self, settings=None):
        super().__init__(settings)
        self.localPath = ""
        self.globalPath = ""
        self.index = None
        self.imports = []
        self.actionLibrary = []
        self.crossreference = []

    def read(self, local, glb=None, index=None):
        if glb is None:
            glb = local
            index = 0
        self.localPath = local
        self.globalPath = glb
        self.index = index
        thk = Thk.parse_file(self.globalPath)
        self.nodes = [NodeDecompiler(ix, self.settings).read(
            node) for ix, node in enumerate(thk.nodeList)]
        self.monster = thk.header.monsterID
        self.labelNodes()
        return self

    def labelNodes(self):
        self.nodeListing = NodeListing()
        validNodes = []
        for node in self.nodes:
            valid = checkEmptyNode(node.node)
            if valid or self.settings.keepVoid:
                if self.settings.forceIndex:
                    node.explicitPosition(True)
                if self.settings.forceId:
                    node.explicitId(True)
                node.label(len(validNodes))
                self.nodeListing.add(node, len(validNodes))
                validNodes.append(node)
        if not valid and self.settings.keepLast:
            node.label(len(validNodes))
            node.explicitPosition(True)
            self.nodeListing.add(node, len(validNodes))
            validNodes.append(node)
        self.validNodes = validNodes
        return self.nodeListing

    def registerUsage(self):
        segmentSet = set()
        for node in self.nodes:
            newRegs = set(sum(map(lambda x: x.registers, node.segments), []))
            segmentSet = segmentSet.union(newRegs)
        self.registers = segmentSet
        return self.registers

    def createEmptyNodes(self, index, *args, **kwargs):
        return self.nodes[index[1]].decompile(*args, position=True, **kwargs)

    def generateHeader(self, entityResolver, scopeResolver):
        imports = scopeResolver.imports()
        header = ""
        if self.settings.listCrossreferences:
            if self.crossreference:
                comments = ["// Xref: "]
                for scopeSource, node in sorted(self.crossreferences):
                    if len(comments[-1]) > 75:
                        comments.append("")
                    scope = "" if scopeSource == "local" else scopeSource + "."
                    comments[-1] += scope + node + ", "
        if self.monster in entityResolver:
            action = self.monsterName
            header += key.IMPORTACT + " %s as %s\n" % (action, action.lower())
        for importSource, importTarget in imports:
            header += key.IMPORTLIB + \
                " %s as %s\n" % (str(importSource), str(importTarget))
        return header+"\n"

    def decompile(self, entityResolver=None,
                  callResolver=None,
                  scopeResolver=None,
                  functionResolver=None,
                  registerScheduler=None):
        if not hasattr(self, "nodeListing"):
            self.labelNodes
        if entityResolver is None:
            actionResolver = loadActionMaps()
            entityResolver = loadEntities(actionResolver)
        if callResolver is None:
            callResolver = CallResolver(
                {55: NodeListing(), self.index: self.nodeListing})
        callResolver.setLocal(self.index)
        if registerScheduler is None:
            registerScheduler = RegisterScheduler(self.settings.forceRegisters)
        if functionResolver is None:
            functionResolver = buildResolver()
        if scopeResolver is None:
            scopeResolver = ScopeResolver()
        if self.monster in entityResolver:
            self.monsterName = entityResolver.getName(self.monster)
            entityResolver[self.monster].scopeName = self.monsterName.lower()
        else:
            self.monsterName = "monster"
        scopeResolver.startContext()
        missingIndices = []
        nodes = ""
        for node in self.validNodes:
            actionResolver = entityResolver[self.monster]
            # node.explicitPosition(True)
            # node.explicitId(False)
            nodes += node.decompile(actionResolver, callResolver,
                                    scopeResolver, functionResolver, registerScheduler)
            missingIndices += node.missingLocalReferences
        # for index in sorted(set(missingIndices)):
        for index in set(missingIndices):
            # print(index)
            nodes += self.createEmptyNodes(index, actionResolver, callResolver,
                                           scopeResolver, functionResolver, registerScheduler)
        return self.generateHeader(entityResolver, scopeResolver) + nodes

    def writeFile(self, *args, **kwargs):
        if self.settings.outputPath is None:
            self.settings.outputPath = str(Path(self.globalPath).parent)
        decompilation = self.decompile(*args, **kwargs)
        folder = self.settings.outputPath
        name = Path(self.globalPath).stem
        with open((Path(folder)/name).with_suffix(".nack"), 'w') as outf:
            outf.write(decompilation)
