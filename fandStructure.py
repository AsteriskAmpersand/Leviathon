# -*- coding: utf-8 -*-
"""
Created on Sun Oct 31 03:02:28 2021

@author: Asterisk
"""

from nackParse import moduleParse
from nackStructures import ActionTarget
from pathlib import Path
from compilerErrors import SemanticError
from errorHandler import ErrorManaged
from compilerUtils import Autonumber

from sly.lex import LexError
import networkx as nx

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
        settings.compiler.root = self.root
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
        for index,module in zip(missingIterator,self.unindexedTargets):
            self.indexedTargets[index] = module
        for index in missingIterator:
            self.indexedTargets[index] = ("",0)
    def calculateSize(self):
        return max(len(self.unindexedTargets) + len(self.indexedTargets),max(self.indexedTargets)) 
    def mapScope(self,fand,thkMap):
        """Map every import to an actual THK Module"""
        parsedScope = {}        
        errorlog = self.errorHandler
        settings = self.settings
        for scope,path in self.scopeNames.items():
            try:
                if Path(path).suffix != ".nack":
                    settings.compiler.incompleteSpecification()
                    parsedScope[scope] = moduleParse(None,thkMap,scope,settings)
                    errorlog.log("Hard Path Found on THK Entry %s : %s"%(scope,path))
                else:
                    if self.settings.compiler.verbose:
                        self.settings.compiler.display("Starting Parsing of %s"%path)
                    path = Path(fand).parent / path
                    #TODO - Try Except on Parses
                    module = moduleParse(path,thkMap,scope,settings,parent = self)
                    parsedScope[scope] = module
            except SyntaxError as e:
                errorlog.thklNameError(e)
            except SemanticError as e:
                errorlog.thkParseError(e)
            except LexError as e:
                print(path,e)
                raise
            except:
                raise
        self.parsedScopes = parsedScope
    def resolveScopeToModule(self):
        for module in self.moduleList.values():
            module.substituteScopes()
            module.resolveScopeToModule(self.moduleList)
    def scopeStringToScopeObject(self,root):
        """Imports are mapped recursively with a project level cache"""
        #Project keeps track of already loaded thk modules
        #Each file keeps track of it's file dependencies
        modules = {str(module.path.absolute()) : module for module in self.parsedScopes.values()}
        for module in self.parsedScopes.values():
            module.scopeStringToScopeObject(root,modules,self.parsedScopes,self.indexedTargets)
        self.moduleList = modules
    def generateDependencyGraph(self):
        errorHandler = self.errorHandler
        depGraph = nx.DiGraph()
        for module in self.moduleList.values():
            for dependency in module.dependencies.values():
                if dependency.inlineCall:
                    depGraph.add_edge(module, dependency)
        if hasCycles(depGraph):
            errorHandler.dependencyCycle()
        self.dependencyGraph = depGraph
        return depGraph
    def mapLocalNodeNames(self):
        errorHandler = self.errorHandler
        for module in self.moduleList.values():
            module.mapLocalNodeNames()
    def resolveModuleInlines(self,module):
        errorHandler = self.errorHandler
        self.settings.compiler.display("\tAnalyzing: "+str(module.path.absolute()))
        for dependency in self.dependencyGraph[module]:
            self.resolveModuleInlines(dependency)
        self.settings.compiler.display("\tResolving Inlines: "+str(module.path.absolute()))
        module.resolveInlines()
    def resolveInlines(self):
        #for module in self.dependencyGraph[module]
        #Resolve immediate variable names on each of the modules
        #If graph is non-cyclical we start from the bottom of dependencies
        #with inline operation resolution
        errorHandler = self.errorHandler
        for module in self.parsedScopes.values():
            if module in self.dependencyGraph:
                self.resolveModuleInlines(module)
    def resolveTerminals(self):
        errorHandler = self.errorHandler
        for module in self.parsedScopes.values():
            if module in self.dependencyGraph:
                module.resolveTerminals()
    def resolveCalls(self):
        for module in self.parsedScopes.values():
            if module in self.dependencyGraph:
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
        registerNames = self.collectRegisters()
        indexedRegisters = [r for r in registerNames if r is int]
        namedRegisters = [r for r in registerNames if r is str and r not in self.registerNames]
        for v in self.registerNames.values():
            if v is not None:
                indexedRegisters.append(v)
        indices = sorted(list(set(indexedRegisters)))
        autoReg = Autonumber(indices)
        ix = 0
        for ix,name in zip(autoReg,namedRegisters):
            self.registerNames[name] = ix
        mix = max(indices, default = 0)
        if mix > 19 or ix > 19:
            self.errorHandler.registryCountExceeded(max(mix,ix))
            return
        for module in self.parsedScopes.values():
            module.resolveRegisters(self.registerNames)
    def compileProperties(self):
        for module in self.parsedScopes.values():
            module.compileProperties()