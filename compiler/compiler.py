# -*- coding: utf-8 -*-
"""
Created on Sun Oct 31 01:45:42 2021

@author: Asterisk
"""

import sys
sys.path.append("..")

from common.monsterEnum import loadEntities
from common.actionEnum import loadActionMaps
from common.fexLayer import buildCompiler
from common.actionEnum import loadTHKMaps
from compiler.compilerErrors import CompilationError
from compiler.errorHandler import ErrorHandler
from compiler.fandLexParse import parseFand
from compiler.compilerSettings import CompilerSettings
from pathlib import Path



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


# incompleteSpecification()
# thkMap
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
        settings.functionResolver = buildCompiler(
            settings.functionResolver).resolve
    if settings.thkMap is None:
        settings.thkMap = loadTHKMaps().moduleToThk


def nackCompile(nack, settings, output=print):
    pass


def parsePhase(fand, settings):
    project, errors = parseFand(fand)
    if errors:
        settings.display("Errors found when parsing:")
        settings.display(fand)
        for error in errors:
            settings.display("\t"+error.replace("sly: ", ""))
        raise CompilationError()
    return project


def fandCompile(fand, settings, output=print):
    try:
        errorHandler = ErrorHandler(settings)

        def report(text):
            if settings.verbose:
                settings.display(text)

        def wrapCall(*outputs):
            if not errorHandler.proceed():
                errorHandler.report()
                raise CompilationError()
            return outputs
        project = parsePhase(fand, settings)
        project.compilerInit(settings, errorHandler)
        thkMap = settings.thkMap
        report("Gathering and Initializing Project Files")
        wrapCall(project.initializeModules(fand, thkMap))
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
        # if settings.verbose:
        #    settings.display(repr(project))
        wrapCall(project.compileProperties())
        project.verify()
        wrapCall(project.serialize(Path(settings.outputRoot)))
        report("Project Compilation Complete")
    except CompilationError:
        if settings.display != print:
            print("Compilation Failed")
        settings.display("Compilation Failed")
    except:
        raise
    return


if __name__ in "__main__":
    def void(*args, **kwargs):
        pass
    errors = []

    def testCompile(folder, file):
        settings = CompilerSettings()
        #settings.verbose = False
        settings.thklistPath = file.stem+".thklst"
        settings.outputRoot = folder
        #settings.display = void
        populateDefaultSettings(settings)
        fandCompile(str(file), settings)
        try:
            fandCompile(str(file), settings)
        except:
            print("Errored", file)
            errors.append(file)

    inRoot = Path(r"D:\Games SSD\MHW-AI-Analysis\Leviathon\tests\ingameFiles")
    outRoot = Path(
        r"D:\Games SSD\MHW-AI-Analysis\Leviathon\tests\ingameOutputs")
    errors = []
    # em_lst = [r"D:\Games SSD\MHW-AI-Analysis\Leviathon\tests\ingameFiles\em045_00_data\em045.fand",
    #          r"D:\Games SSD\MHW-AI-Analysis\Leviathon\tests\ingameFiles\em114_00_data\em114.fand"]
    #ems_lst = []
    #lst = list(map(Path,em_lst + ems_lst))# ))#
    lst = list(inRoot.rglob("*.fand"))
    lst = []
    for path in lst:
        print(path)
        s = path.relative_to(inRoot).parent
        (outRoot/s).mkdir(parents=True, exist_ok=True)
        #testCompile(path.parent/"Compiled", path)
        testCompile(str(outRoot/s), (path))

    #fandCompile(r"D:\Games SSD\MHW-AI-Analysis\Leviathon\tests\ingameFiles\em007_00_data\em007.fand",settings)
    lst = [
        Path(r'C:\Users\Asterisk\Documents\ICETest\AlexandermothProject\em\em121\00\data\em121.fand'),
        ]
    for path in lst:
        print(path)
        s = path.parent
        (s/"compiled").mkdir(parents=True, exist_ok=True)
        testCompile(path.parent/"Compiled", path)
