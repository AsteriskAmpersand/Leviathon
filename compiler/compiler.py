# -*- coding: utf-8 -*-
"""
Created on Sun Oct 31 01:45:42 2021

@author: Asterisk
"""

from pathlib import Path

from compiler.compilerSettings import CompilerSettings
from compiler.fandLexParse import parseFand
from compiler.errorHandler import ErrorHandler

from common.actionEnum import loadTHKMaps
from common.fexLayer import buildCompiler
from common.actionEnum import loadActionMaps
from common.monsterEnum import loadEntities


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
    if settings.entityMap is None:
        actionResolver = loadActionMaps()
    else:
        actionResolver = loadActionMaps(settings.entityMap)
    entityResolver = loadEntities(actionResolver)
    settings.entityMap = entityResolver
    if settings.functionResolver is None:
        settings.functionResolver = buildCompiler().resolve    
    else:
        settings.functionResolver = buildCompiler(settings.functionResolver).resolve        
    if settings.thkMap is None:
        settings.thkMap = loadTHKMaps().moduleToThk

class CompilationError(Exception):
    pass

def nackCompile(nack,settings,output = print):
    pass

def fandCompile(fand,settings,output = print):
    try:
        errorHandler = ErrorHandler(settings)
        def report(text):
            if settings.verbose:settings.display(text)
        def wrapCall(*outputs):
            if not errorHandler.proceed():
                errorHandler.report()
                raise CompilationError()
            return outputs
        project = parseFand(fand)
        project.compilerInit(settings,errorHandler)
        thkMap = settings.thkMap
        report("Gathering and Initializing Project Files")
        wrapCall(project.initializeModules(fand,thkMap))
        report("Creating Symbols Tables")
        wrapCall(project.createSymbolsTables(Path(fand).absolute().parent))
        report("Resolving Local Namespaces")
        wrapCall(project.resolveLocal())
        report("Resolving Inline Invocations")
        wrapCall(project.resolveInlines())
        wrapCall(project.resolveTerminal())
        report("Resolving Calls")
        wrapCall(project.resolveCalls())
        report("Resolving Actions")
        wrapCall(project.resolveActions(settings.entityMap))
        report("Resolving Register Names")
        wrapCall(project.resolveRegisters())
        report("Resolving Function Names")
        wrapCall(project.resolveFunctions(settings.functionResolver))
        report("Compiling to Binary")
        wrapCall(project.compileProperties())
        wrapCall(project.serialize(Path(settings.outputRoot)))
        report("Project Compilation Complete")
    except CompilationError:
        pass
    except:
        raise
    return
    
if __name__ in "__main__":
    def void(*args,**kwargs):
        pass
    
    def testCompile(folder,file):
        ts = CompilerSettings()
        
        settings = CompilerSettings()
        settings.verbose = False
        settings.thklistPath = file.stem+".thklst"
        settings.outputRoot = folder
        ts.display = void
        populateDefaultSettings(settings)
        fandCompile(file,ts)
        

    inRoot = Path(r"D:\Games SSD\MHW-AI-Analysis\Leviathon\tests\ingameFiles")
    outRoot = Path(r"D:\Games SSD\MHW-AI-Analysis\Leviathon\tests\ingameOutputs")
    errors = []
    lst = list(inRoot.rglob("*.fand"))
    for path in lst:
        s = path.parent.stem
        (outRoot/s).mkdir(parents = True, exist_ok = True)
        try:
            testCompile(str(outRoot/s),str(path))
        except:
            testCompile(str(outRoot/s),str(path))
            try:
                testCompile(str(outRoot/s),str(path))
            except:
                print ("Errored",path)
                errors.append(path)
                #raise
                
    #fandCompile(r"D:\Games SSD\MHW-AI-Analysis\KushalaTest\em024.fand",settings)