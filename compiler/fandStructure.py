# -*- coding: utf-8 -*-
"""
Created on Sun Oct 31 03:02:28 2021

@author: Asterisk
"""

from compiler.nackParse import moduleParse
from compiler.nackStructures import ActionTarget
from compiler.errorHandler import ErrorManaged
from compiler.compilerErrors import CompilationError
from compiler.compilerUtils import Autonumber
from common import thklist

from pathlib import Path
import queue
import json

THK_Enumeration = {"THK_%02d" % ix: ix for ix in range(100)}


class FandStructure(ErrorManaged):
    tag = "FandFile"

    def __init__(self):
        self.root = None
        self.relative = None
        self.monster = None
        self.registerNames = {}
        self.unindexedTargets = {}
        self.indexedTargets = {}
        self.scopeNames = {}
        self.count = -1

    def verify(self):
        for project in set(self.parsedScopes.values()):
            project.verify()
        #list(map(lambda x: x.verify(), project.modules.values()))

    def compilerInit(self, settings, errorLog):
        settings.root = self.root
        self.inherit(settings, errorLog)
        self.performIndexation()

    def performIndexation(self):
        if self.count == -1:
            self.count = self.calculateSize()
        newIndexations = set()
        for scopename, path, specifier in self.unindexedTargets.values():
            if scopename in self.settings.thkMap:
                ix = self.settings.thkMap[scopename]
            elif scopename in THK_Enumeration:
                ix = THK_Enumeration[scopename]
            else:
                continue
            if ix not in self.indexedTargets:
                self.indexedTargets[ix] = (scopename, path, specifier)
                newIndexations.add(scopename)
        missing = []
        for index in range(self.count):
            if index not in self.indexedTargets:
                missing.append(index)
        missingIterator = iter(missing)
        for scopename in reversed(self.unindexedTargets):
            if scopename not in newIndexations:
                index = next(missingIterator)
                self.indexedTargets[index] = self.unindexedTargets[scopename]
        for index in missingIterator:
            self.indexedTargets[index] = ("", "", 0)

    def calculateSize(self):
        return max(len(self.scopeNames), max(self.indexedTargets, default=0))

    def parseModule(self, path, scope, thkMap):
        if self.settings.verbose:
            self.settings.display("Starting Parsing of %s" % path)
        if str(path) not in self.modules:
            module = moduleParse(
                path, thkMap, scope, self.settings, parent=self, external=not bool(scope))
            self.modules[str(path)] = module
            self.inheritChildren(module)
        else:
            module = self.modules[str(path)]
        if scope:
            self.parsedScopes[scope] = module
        return module

    def initializeModules(self, fand, thkMap):
        """Map every import to an actual THK Module"""
        self.parsedScopes = {}
        self.modules = {}
        self.rootFolder = Path(fand).absolute().parent
        moduleParsingQueue = queue.Queue()
        for scope, path in self.scopeNames.items():
            moduleParsingQueue.put((scope, path))
        while not moduleParsingQueue.empty():
            scope, path = moduleParsingQueue.get()
            if Path(path).suffix != ".nack":
                # self.settings.incompleteSpecification()
                module = self.parsedScope[scope] = moduleParse(
                    None, thkMap, scope, self.settings)
                self.errorHandler.compiledModule(scope, path)
            else:
                path = Path(fand).parent / path
                try:
                    module = self.parseModule(path, scope, thkMap)
                    for dependency in module.externalDependencies():
                        dependencyPath = str(self.rootFolder/dependency)
                        if dependencyPath not in self.modules:
                            moduleParsingQueue.put(("", dependencyPath))
                except CompilationError:
                    self.modules[scope] = None
                    self.errorHandler.lexingFail(path)

    def createSymbolsTables(self, root):
        for module in self.modules.values():
            module.createSymbolsTable(
                root, self.parsedScopes, self.modules, self.indexedTargets)

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
        # for module in self.dependencyGraph[module]
        # Resolve immediate variable names on each of the modules
        # If graph is non-cyclical we start from the bottom of dependencies
        # with inline operation resolution
        for module in self.parsedScopes.values():
            if self.settings.verbose:
                self.settings.display(
                    "\tResolving Inlines: "+str(module.path.absolute()))
            module.resolveInlines()

    def resolveTerminal(self):
        for module in self.parsedScopes.values():
            module.resolveTerminal()

    def resolveCalls(self):
        for module in self.parsedScopes.values():
            module.resolveCalls()

    def resolveActions(self, entityMap):
        projectMonster = self.inheritChildren(
            ActionTarget(self.monster, "project"))
        projectMonster.resolve(entityMap)
        for module in self.parsedScopes.values():
            module.resolveActions(entityMap, projectMonster)

    def collectRegisters(self):
        registerNames = set()
        for module in self.parsedScopes.values():
            registerNames = registerNames.union(module.collectRegisters())
        return registerNames

    def resolveRegisters(self):
        registerNames = list(
            sorted(self.collectRegisters(), key=lambda x: str(x)))
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
        mix = max(indices, default=0)
        if mix > 21 or ix > 21:
            self.errorHandler.registryCountExceeded(max(mix, ix),
                                                    registerNames)
            return
        for module in self.parsedScopes.values():
            module.resolveRegisters(self.registerNames)

    def resolveFunctions(self, functionResolver):
        for module in self.parsedScopes.values():
            module.resolveFunctions(functionResolver)

    def compileProperties(self):
        for name,module in self.parsedScopes.items():
            module.compileProperties()

    def buildEntry(self, moduleName):
        tTDH = thklist.thinkTableDataHash
        tth = 0
        outpath = ''
        if moduleName:
            tth = thklist.thinkTableHash
            outpath = moduleName.replace("/", "\\")
        return {"thinkTableDataHash": tTDH, "rThinkTableHash": tth, "path": outpath}

    def serializeModule(self, outRoot, scopeName, module, scopeToIndex,
                        previousPaths, previousFiles):
        absp = module.path.absolute()
        if self.settings.projectNames == "function":
            result = scopeName
        elif self.settings.projectNames == "nackFile":
            result = module.path.stem
        elif self.settings.projectNames == "index":
            result = "%s_%02d" % (
                Path(self.settings.thklistPath).stem, scopeToIndex[scopeName])
        else:
            raise KeyError("Invalid Project Naming Setting")
        thklPath = self.relative + "\\" + result
        if absp in previousFiles:
            previousPaths[scopeName] = previousFiles[absp]
            return
        else:
            previousPaths[scopeName] = thklPath
        previousFiles[absp] = thklPath
        module.serialize(outRoot, result + ".thk")
        return

    def serialize(self, outRoot):
        # "function","nackfile","index"
        scopeToIndex = {tern[0]: index for index,
                        tern in self.indexedTargets.items()}
        previousPaths, previousFiles = {}, {}
        for scopeName, module in \
                sorted(self.parsedScopes.items(), key=lambda x: scopeToIndex[x[0]]):
            self.serializeModule(outRoot, scopeName, module, scopeToIndex,
                                 previousPaths, previousFiles)
        count = len(self.indexedTargets)
        header = {"signature": thklist.signature, "count": count}
        data = [self.indexedTargets[i][2] for i in range(count)]
        entries = []
        for i in range(count):
            if self.indexedTargets[i][0] in previousPaths:
                targetString = previousPaths[self.indexedTargets[i][0]]
            else:
                targetString = ""
            entries.append(self.buildEntry(targetString))
        binaryData = thklist.ThkList.build(
            {"header": header, "data": data, "entries": entries})
        outpath = outRoot/(self.settings.thklistPath)
        outpath.parent.mkdir(parents=True, exist_ok=True)
        with open(outpath, 'wb') as outf:
            outf.write(binaryData)

    def exportSymbols(self, outRoot):
        outpath = outRoot/(self.settings.symbolsPath)
        fileIndices = {}
        monster = self.monster
        monsterID = None
        scopeToIndex = {tern[0]: index for index,
                        tern in self.indexedTargets.items()}
        for scopeName, module in \
                sorted(self.parsedScopes.items(), key=lambda x: scopeToIndex[x[0]]):
            index = scopeToIndex[scopeName]
            monsterID = module.parsedStructure.monsterID
            fileIndices[index] = {"name":scopeName, "module":module.exportSymbols(),
                                  "path":str(module.path), "monster":monsterID}
        project = {"monster":monsterID if monsterID is not None else -1,
                   "files":fileIndices}
        #self.parsedScopes.items()
        obj = fileIndices
        with open(outpath,"w") as outf:
            json.dump(obj, outf)
        return

    def __repr__(self):
        spacer = '\n======================================\n\n'
        return spacer.join((repr(m.parsedStructure) for m in self.modules.values()))