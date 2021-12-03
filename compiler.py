# -*- coding: utf-8 -*-
"""
Created on Sun Oct 31 01:45:42 2021

@author: Asterisk
"""

from pathlib import Path

from transpilerSettings import TranspilerSettings
from fandLexParse import parseFand
from nackParse import parseNack
from fexLayer import buildCompiler
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
    if settings.compiler.functionResolver is None:
        settings.compiler.functionResolver = buildCompiler().resolve
        #TODO - Parse Fexxty file and obtain the resolution object
        #Should bedone by the settings parser as well
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
    report("Gathering and Initializing Project Files")
    wrapCall(project.initializeModules(fand,thkMap))
    report("Create Symbols Tables")
    wrapCall(project.createSymbolsTables(Path(fand).absolute().parent))
    report("Resolving Local Namespaces")
    wrapCall(project.resolveLocal())
    report("Resolving Inline Invocations")
    wrapCall(project.resolveInlines())
    wrapCall(project.resolveTerminal())
    report("Resolving Calls")
    wrapCall(project.resolveCalls())
    report("Resolving Actions")
    wrapCall(project.resolveActions(settings.compiler.entityMap))
    report("Resolving Register Names")
    wrapCall(project.resolveRegisters())
    report("Resolving Function Names")
    wrapCall(project.resolveFunctions(settings.compiler.functionResolver))
    report("Compiling to Binary")
    wrapCall(project.compileProperties())
    wrapCall(project.serialize(Path(settings.compiler.outputRoot)))
    report("Project Compilation Complete")
    return
    
if __name__ in "__main__":
    settings = TranspilerSettings()
    settings.compiler.verbose = True
    settings.compiler.thklistPath = r"test.thklist"
    settings.compiler.outputRoot = r"D:\Games SSD\MHW-AI-Analysis\TestOutput"
    populateDefaultSettings(settings)
    fandCompile(r"D:\Games SSD\MHW-AI-Analysis\InlineTest\em001.fand",settings)