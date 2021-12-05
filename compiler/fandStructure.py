# -*- coding: utf-8 -*-
"""
Created on Sun Oct 31 03:02:28 2021

@author: Asterisk
"""

from Leviathon.compiler.nackParse import moduleParse
from Leviathon.compiler.nackStructures import ActionTarget
from Leviathon.compiler.errorHandler import ErrorManaged
from Leviathon.compiler.compilerUtils import Autonumber
from Leviathon.common import thklist

from pathlib import Path
import networkx as nx
import queue

def hasCycles(g):
    try:
        nx.find_cycle(g)
    except:
        return False
    return True

class FandStructure(ErrorManaged):
    tag = "FandFile"
    def __init__(self):
        self.root = None
        self.relative = None
        self.monster = None
        self.registerNames = {}
        self.unindexedTargets = []
        self.indexedTargets = {}
        self.scopeNames = {}
        self.count = -1
    def compilerInit(self,settings,errorLog):
        settings.root = self.root
        self.performIndexation()
        self.inherit(settings,errorLog)
    def performIndexation(self):
        if self.count == -1:
            self.count = self.calculateSize()
        missing = []
        for index in range(self.count):
            if index not in self.indexedTargets:
                 missing.append(index)
        missingIterator = iter(missing)
        for module in self.unindexedTargets:
            index = next(missingIterator)
            self.indexedTargets[index] = module
        for index in missingIterator:
            self.indexedTargets[index] = ("",0)
    def calculateSize(self):
        return max(len(self.unindexedTargets) + len(self.indexedTargets),max(self.indexedTargets))
    def parseModule(self,path,scope,thkMap):
        if self.settings.verbose:
            self.settings.display("Starting Parsing of %s"%path)
        if str(path) not in self.modules:
            module = moduleParse(path,thkMap,scope,self.settings,parent = self,external = not bool(scope))
            self.modules[str(path)] = module
            self.inheritChildren(module)
        else:
            module = self.modules[str(path)]
        if scope:
            self.parsedScopes[scope] = module
        return module
    def initializeModules(self,fand,thkMap):
        """Map every import to an actual THK Module"""        
        self.parsedScopes = {}
        self.modules = {}
        self.rootFolder = Path(fand).absolute().parent
        moduleParsingQueue = queue.Queue()
        for scope,path in self.scopeNames.items(): moduleParsingQueue.put((scope,path))
        while not moduleParsingQueue.empty():
            scope,path = moduleParsingQueue.get()
            if Path(path).suffix != ".nack":
                #self.settings.incompleteSpecification()
                module = self.parsedScope[scope] = moduleParse(None,thkMap,scope,self.settings)
                self.errorHandler.compiledModule(scope,path)
            else:
                path = Path(fand).parent / path
                module = self.parseModule(path,scope,thkMap)
                for dependency in module.externalDependencies():
                    dependencyPath = str(self.rootFolder/dependency)
                    if dependencyPath not in self.modules:
                        moduleParsingQueue.put(("",dependencyPath))
    def createSymbolsTables(self,root):
        for module in self.modules.values():
            module.createSymbolsTable(root,self.parsedScopes,self.modules,self.indexedTargets)
    def resolveImmediates(self):
        for module in self.modules.values():
            module.resolveImmediates(self.parsedSscopes)
    def resolveScopeToModule(self):
        for module in self.modules.values():
            module.substituteScopes()
            module.resolveScopeToModule(self.modules)
    def resolveLocal(self):
        for module in self.modules.values():
            module.resolveLocal()
    def resolveInlines(self):
        #for module in self.dependencyGraph[module]
        #Resolve immediate variable names on each of the modules
        #If graph is non-cyclical we start from the bottom of dependencies
        #with inline operation resolution
        for module in self.parsedScopes.values():
            if self.settings.verbose:
                self.settings.display("\tResolving Inlines: "+str(module.path.absolute()))
            module.resolveInlines()
    def resolveTerminal(self):
        for module in self.parsedScopes.values():
            module.resolveTerminal()
    def resolveCalls(self):
        for module in self.parsedScopes.values():
            module.resolveCalls()
    def resolveActions(self,entityMap):
        projectMonster = self.inheritChildren(ActionTarget(self.monster,"project"))
        projectMonster.resolve(entityMap)
        for module in self.parsedScopes.values():
            module.resolveActions(entityMap,projectMonster)
    def collectRegisters(self):
        registerNames = set()
        for module in self.parsedScopes.values():
            registerNames = registerNames.union(module.collectRegisters())
        return registerNames
    def resolveRegisters(self):
        registerNames = list(sorted(self.collectRegisters()))
        indexedRegisters = [r for r in registerNames if type(r) is int]
        namedRegisters = [r for r in registerNames if type(r) is str and 
                          not (r in self.registerNames and self.registerNames[r] is not None)]
        for v in self.registerNames.values():
            if v is not None:
                indexedRegisters.append(v)
        indices = sorted(list(set(indexedRegisters)))
        autoReg = Autonumber(indices)
        ix = 0
        for name in namedRegisters:
            ix = next(autoReg)
            self.registerNames[name] = ix
        mix = max(indices, default = 0)
        if mix > 19 or ix > 19:
            self.errorHandler.registryCountExceeded(max(mix,ix))
            return
        for module in self.parsedScopes.values():
            module.resolveRegisters(self.registerNames)
    def resolveFunctions(self,functionResolver):
        for module in self.parsedScopes.values():
            module.resolveFunctions(functionResolver)
    def compileProperties(self):
        for module in self.parsedScopes.values():
            module.compileProperties()
    def buildEntry(self,moduleName):
        tTDH = thklist.thinkTableDataHash
        tth = 0
        outpath = ''
        if moduleName:
            tth = thklist.thinkTableHash
            outpath = (self.relative + "\\" + str(Path(moduleName).with_suffix(".thk"))).replace("/","\\")
        return {"thinkTableDataHash":tTDH,"rThinkTableHash":tth,"path":outpath}
    def serialize(self,outRoot):
        for path,module in self.parsedScopes.items():
            outpath = Path(path).stem + ".thk"
            module.serialize(outRoot,outpath)
        count = len(self.indexedTargets)
        header = {"signature":thklist.signature,"count":count}
        data = [self.indexedTargets[i][1] for i in range(count)]
        entries = [self.buildEntry(self.indexedTargets[i][0]) for i in range(count)]
        binaryData = thklist.ThkList.build({"header":header,"data":data,"entries":entries})
        with open(outRoot/(self.settings.thklistPath),'wb') as outf:
            outf.write(binaryData)
    def __repr__(self):
        spacer = '\n======================================\n\n'
        return spacer.join((repr(m.parsedStructure) for m in self.modules.values()))