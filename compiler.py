# -*- coding: utf-8 -*-
"""
Created on Sun Oct 31 01:45:42 2021

@author: Asterisk
"""

from pathlib import Path

from transpilerSettings import TranspilerSettings
from fandLexParse import parseFand
from nackParse import parseNack
from compilerErrors import SemanticError
from actionEnum import loadActionMaps,loadTHKMaps

import re

# class FandStructure():
#     def __init__(self):
#         self.root = None
#         self.relative = None
#         self.monster = None
#         self.registerNames = {}        
#         self.unindexedTargets = []
#         self.indexedTargets = {}        
#         self.scopeNames = {}        
#         self.count = -1            

class ErrorHandler():
    def __init__(self,settings):
        self.settings = settings
        self.mark = False
        self.trace = []
        self.errorlog = []
    def thklNameError(self,exception):
        pass
    def thkParseError(self,exception):
        pass
    def proceed(self):
        return not self.mark
    def log(self,string):
        self.log.append(string)
    def report(self):
        for entry in self.errorlog:
            print(entry)

#incompleteSpecification()
#thkMap
def populateDefaultSettings(settings):
    if settings.compiler.thkMap is None:
        settings.compiler.thkMap = loadTHKMaps().moduleToThk

class CompilationError(Exception):
    pass

def fandCompile(fand,settings,output = print):
    errorHandler = ErrorHandler(settings)
    def wrapCall(*outputs):
        if not errorHandler.proceed():
            errorHandler.report()
            raise CompilationError()
        return outputs
    project = parseFand(fand)
    project.compilerInit(settings,errorHandler)
    thkMap = settings.compiler.thkMap
    wrapCall(project.mapScope(fand,thkMap))
    wrapCall(project.resolveScopeNames(Path(fand).absolute().parent))
    graph = wrapCall(project.generateDependencyGraph())
    wrapCall(project.mapLocalNodeNames())
    wrapCall(project.resolveInlines())
    wrapCall(project.resolveTerminals())
    #TODO
    project.resolveNodeNames()
    #project.resolveIdentifiers()#No way of actually resolving the notion of variables
    project.resolveCalls()
    project.resolveActions()
    project.resolveRegisters()
    project.resolveFunctions()#God have mercy
    project.resolveSegments()
    project.resolveNodes()
    project.serialize()
    return
    
    
    #project.substituteScopes()
    project.resolveInlines()
    
if __name__ in "__main__":
    settings = TranspilerSettings()
    settings.compiler.verbose = True
    populateDefaultSettings(settings)
    fandCompile(r"D:\Games SSD\MHW-AI-Analysis\InlineTest\em001.fand",settings)