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
    errors = []
    
    def testCompile(folder,file):        
        settings = CompilerSettings()
        settings.verbose = False
        settings.thklistPath = file.stem+".thklst"
        settings.outputRoot = folder
        #settings.display = void
        populateDefaultSettings(settings)
        try:
            fandCompile(str(file),settings)
        except:
            print("Errored",file)
            errors.append(file)

    inRoot = Path(r"D:\Games SSD\MHW-AI-Analysis\Leviathon\tests\ingameFiles")
    outRoot = Path(r"D:\Games SSD\MHW-AI-Analysis\Leviathon\tests\ingameOutputs")
    errors = []
    lst = ['D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\em023_00_data\\em023.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\em023_05_data\\em023.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\em050_00_data\\em050.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\em100_01_data\\em100.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\em102_00_data\\em102.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\em102_00_data\\em102_sub03.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\em104_00_data\\em104.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\em109_01_data\\em109.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\em110_01_data\\em110.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\em113_00_data\\em113.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\em113_01_data\\em113.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\em118_00_data\\em118.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\em118_05_data\\em118.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\em121_00_data\\em121.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\em126_00_data\\em126.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems003_00_data\\ems003.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems003_05_data\\ems003.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems004_00_data\\ems004.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems004_00_data_event_q61605\\ems004.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems005_01_data\\ems005.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems006_00_data\\ems006.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems014_00_data\\ems014.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems016_00_data\\ems016.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems029_00_data\\ems029.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems049_00_data\\ems049.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems049_00_data\\ems049_sub03.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems049_00_data\\ems049_sub10.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems049_00_data_event_st101_f\\ems049.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems049_00_data_event_st101_g\\ems049.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems049_00_data_event_tutorial\\ems049.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems049_00_data_event_tutorial\\ems049_90.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems049_00_data_event_tutorial\\ems049_91.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems049_00_data_event_tutorial\\ems049_92.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems051_00_data\\ems051.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems051_05_data\\ems051.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems053_00_data\\ems053.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems054_00_data\\ems054.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems055_00_data\\ems055.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems055_00_data_event_q00001\\ems055.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems055_00_data_event_q00401\\ems055.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems055_00_data_event_q00504\\ems055.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems056_00_data\\ems056.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems058_00_data\\ems058.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems059_00_data\\ems059.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems060_00_data\\ems060.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems060_00_data\\ems060_401.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems060_01_data\\ems060.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems060_01_data\\ems060_401.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems061_00_data\\ems061.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems061_01_data\\ems061.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems062_00_data\\ems062.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems062_01_data\\ems062.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems062_02_data\\ems062.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems062_03_data\\ems062.fand',
             'D:\\Games SSD\\MHW-AI-Analysis\\Leviathon\\tests\\ingameFiles\\ems064_00_data\\ems064.fand']
    lst = list(inRoot.rglob("*.fand"))
    #lst = [Path(r"D:\Games SSD\MHW-AI-Analysis\Leviathon\tests\ingameFiles\em007_00_data\em007.fand")]
    for path in lst:
       # print(path)
        s = path.parent.stem
        (outRoot/s).mkdir(parents = True, exist_ok = True)
        try:
            testCompile(str(outRoot/s),(path))
        except:
            testCompile(str(outRoot/s),(path))
            try:
                testCompile(str(outRoot/s),(path))
            except:
                print ("Errored",path)
                errors.append(path)
                #raise
                
    #fandCompile(r"D:\Games SSD\MHW-AI-Analysis\Leviathon\tests\ingameFiles\em007_00_data\em007.fand",settings)