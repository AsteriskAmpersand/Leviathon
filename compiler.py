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
from monsterEnum import loadEntities
from errorHandler import ErrorHandler,ErrorManaged

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



#incompleteSpecification()
#thkMap
def populateDefaultSettings(settings):
    if settings.compiler.thkMap is None:
        settings.compiler.thkMap = loadTHKMaps().moduleToThk

class CompilationError(Exception):
    pass

def fandCompile(fand,settings,output = print):
    #TODO - Remove after testing, the settings parser should take care of this
    if settings.compiler.entityMap is None:
        actionResolver = loadActionMaps()
        entityResolver = loadEntities(actionResolver)
        settings.compiler.entityMap = entityResolver
    #
    
    
    errorHandler = ErrorHandler(settings)
    def report(text):
        if settings.compiler.verbose:settings.compiler.display(text)
    def wrapCall(*outputs):
        if not errorHandler.proceed():
            errorHandler.report()
            raise CompilationError()
        return outputs
    project = parseFand(fand)
    project.compilerInit(settings,errorHandler)
    thkMap = settings.compiler.thkMap
    report("Enumerating Scopes")
    wrapCall(project.mapScope(fand,thkMap))
    report("Resolving Scopes")
    wrapCall(project.scopeStringToScopeObject(Path(fand).absolute().parent))
    wrapCall(project.resolveScopeToModule())
    report("Generating Dependency Graph")
    graph = wrapCall(project.generateDependencyGraph())
    report("Mapping Local Namespaces")
    wrapCall(project.mapLocalNodeNames())
    report("Resolving Inline Invocations")
    wrapCall(project.resolveInlines())
    wrapCall(project.resolveTerminals())
    report("Resolving Calls")
    project.resolveCalls()
    report("Resolving Actions")
    project.resolveActions(settings.compiler.entityMap)
    report("Resolving Register Names")
    project.resolveRegisters()
    report("Resolving Function Names")
    #TODO
    project.resolveFunctions()#God have mercy
    report("Compiling to Binary")
    project.resolveSegments()
    project.resolveNodes()
    project.serialize()
    report("Project Compilation Complete")
    return
    
    
    #
    project.resolveInlines()
    
if __name__ in "__main__":
    settings = TranspilerSettings()
    settings.compiler.verbose = True
    populateDefaultSettings(settings)
    fandCompile(r"D:\Games SSD\MHW-AI-Analysis\InlineTest\em001.fand",settings)