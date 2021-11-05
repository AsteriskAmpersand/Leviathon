# -*- coding: utf-8 -*-
"""
Created on Sun Oct 31 03:02:28 2021

@author: Asterisk
"""

from nackParse import moduleParse
from pathlib import Path
from compilerErrors import SemanticError
from sly.lex import LexError
import networkx as nx

def hasCycles(g):
    try:
        nx.find_cycle(g)
    except:
        return False
    return True

class FandStructure():
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
        self.settings = settings
        self.errorHandler = errorLog
        self.performIndexation()
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
                    path = Path(fand).parent / path
                    module = moduleParse(path,thkMap,scope,settings)
                    module.substituteScopes()
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
    def substituteScopes(self):
        for scope in self.parsedScopes.values():
            scope.substituteScopes()
    def resolveScopeNames(self,root):
        """Imports are mapped recursively with a project level cache"""
        #Project keeps track of already loaded thk modules
        #Each file keeps track of it's file dependencies
        modules = {module.path.absolute() : module for module in self.parsedScopes.values()}
        for module in self.parsedScopes.values():
            module.resolveScopeNames(root,modules,self.parsedScopes,self.indexedTargets,self.settings)
        self.moduleList = modules
    def generateDependencyGraph(self):
        errorHandler = self.errorHandler
        depGraph = nx.DiGraph()
        for module in self.parsedScopes.values():
            for dependency in module.dependencies.values():
                if not dependency.inlineCall:
                    depGraph.add_edge(module, dependency)
        if hasCycles(depGraph):
            errorHandler.dependencyCycle()
        self.dependencyGraph = depGraph
        return depGraph
    def mapLocalNodeNames(self):
        errorHandler = self.errorHandler
        for module in self.moduleList.values():
            module.mapLocalNodeNames(errorHandler)
    def resolveNodeInlines(self,node):
        errorHandler = self.errorHandler
        for dependency in self.dependencyGraph[node]:
            self.resolveNodeInLines(dependency)
        node.resolveInlines()
    def resolveInlines(self):
        errorHandler = self.errorHandler
        for module in self.parsedScopes.values():
            if module in self.dependencyGraph:
                self.resolveNodeInLines(module)
                
                #for module in self.dependencyGraph[module]
            
        raise
        #TODO
        #Resolve immediate variable names on each of the modules
    #If graph is non-cyclical we start from the bottom of dependencies
    #with inline operation resolution