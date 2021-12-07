# -*- coding: utf-8 -*-
"""
Created on Tue Dec  7 06:26:07 2021

@author: Asterisk
"""

from pathlib import Path
from collections import Counter

from common import thklSpecStr as thklSpec
from common.thk import Header
from common.thklist import ThkList
from common.fexLayer import buildResolver
from common.actionEnum import loadActionMaps, loadTHKMaps
from common.monsterEnum import loadEntities
from decompiler.codeAnalysis import THKProject, rootMatch, cojoinedMatching
from decompiler.thkDecompiler import THKDecompiler
from decompiler.decompilerUtils import Decompiler
from decompiler.thkDecompileUtils import CallResolver, ScopeResolver, RegisterScheduler
# Decompilation

# Load THKL
# Load THKs
# Perform Local Node Naming and Enumeration
# Map each file naming and enumeration (Scoped name on import, THK > THKL > THKRef (so scope is named after the THKL label for the file)
# Resolve Actions Locally for each file (Add Comments if a call is void) (Allow the decompiler to use customized mappings)
# Resolve Calls to Scope + Name or Name if local (Add Comments if a call is void) (Is it just passing a dict with Index -> Scope Name, Node# -> Function Name)
# Resolve Function Checks through the Specification  (from  the FExtY file)


class THKLEntry():
    def __init__(self, index, metadata, partialPath=None, fullPath=None):
        self.valid = partialPath is not None
        self.index = index
        self.metadata = metadata
        self.partialPath = partialPath
        self.fullPath = fullPath


class THKLDecompiler(Decompiler):
    def __init__(self, settings=None):
        super().__init__(settings)
        self.setup = False

    def consensusLocation(self, thklist):
        roots = Counter()
        for thkp in thklist:
            if thkp.valid:
                match = rootMatch(Path(self.path), Path(thkp.partialPath))
                if match:
                    roots[match] += 1
        if roots:
            return next(iter(roots.most_common()))[0]
        else:
            return self.path.parent

    def consensusFolder(self, thklist):
        roots = Counter()
        for thkp in thklist:
            if thkp.valid:
                for p in Path(thkp.partialPath).parents:
                    roots[p] += 1
        if roots:
            return str(next(iter(sorted(roots.items(), key=lambda x: (-x[1], -len(str(x[0]))))))[0])
        else:
            return ""

    def consensusMonster(self, thklist):
        monster = Counter()
        for thkp in thklist:
            if thkp.valid:
                if Path(thkp.fullPath).exists():
                    thkh = Header.parse_file(thkp.fullPath)
                    monster[(thkh.monsterID, thkh.isPalico)] += 1
        if monster:
            monId, palico = next(iter(monster.most_common()))[0]
            if not palico:
                return self.entityMap.getName(monId)
            else:
                return "Palico"
        else:
            return None

    def read(self, path):
        self.path = Path(path)
        thkl = ThkList.parse_file(path)
        self.thkl = [self.thkPathParse(ix, e.path+".thk" if e.path else "", d)
                     for ix, (e, d) in enumerate(zip(thkl.entries, thkl.data))]
        self.thkFiles = [THKDecompiler(self.settings).read(
            thk.partialPath, thk.fullPath, thk.index) for thk in self.thkl if thk.valid]
        return self

    def thkPathParse(self, ix, thkpath, d):
        if not thkpath:
            return THKLEntry(ix, d)
        matchedthkpath = Path(thkpath)
        matchedthkpath = cojoinedMatching(self.path, matchedthkpath)
        return THKLEntry(ix, d, thkpath, matchedthkpath)

    def decompile(self, entityMap=None, thkMap=None, functionResolver=None):
        if not self.setup:
            self.setupStructures(entityMap, thkMap, functionResolver)
        result = ""
        if self.location:
            result += (thklSpec.chunk_str % self.location) + "\n"
        if self.folder is not None:
            result += (thklSpec.filepath_str % self.folder) + "\n"
        if self.monster:
            result += thklSpec.monster_str % self.monster + "\n"
        if result:
            result += "\n"
        result += self.registerScheduler.declarations(
            self.settings.keepRegisters)
        self.fileNames = []
        for thk in self.thkl:
            if thk.valid:
                if self.settings.functionAsThkName:
                    partial = Path(self.scopeNamer.resolve(
                        thk.index).lower()+".nack")
                else:
                    try:
                        partial = Path(thk.partialPath).relative_to(
                            self.folder).with_suffix(".nack")
                    except:
                        partial = Path(thk.partialPath).with_suffix(".nack")
                self.fileNames.append(partial)
                result += thklSpec.function_str % (
                    self.scopeNamer.resolve(thk.index), partial, thk.metadata) + "\n"
        if self.settings.verbose:
            self.settings.display("")
        result += thklSpec.length_str % len(self.thkl)
        return result

    def buildCallResolver(self):
        callResolver = CallResolver()
        for thk in self.thkFiles:
            callResolver[thk.index] = thk.nodeListing
            # print(thk.nodeListing.rawIndexToNode.keys())
            # raise
        self.callResolver = callResolver
        return callResolver

    def buildScopeResolver(self):
        scopeResolver = ScopeResolver()
        for thk in self.thkFiles:
            scopeResolver.addEntry(
                thk.index, self.scopeNamer.resolve(thk.index))
        self.scopeResolver = scopeResolver
        return scopeResolver

    def buildRegisterScheduler(self):
        registers = set()
        for thk in self.thkFiles:
            registers = registers.union(thk.registerUsage())
        regSched = RegisterScheduler(self.settings.forceRegisters)
        for ix, register in enumerate(sorted(registers)):
            regSched.label(register, "RegisterVar%d" % ix)
        self.registerScheduler = regSched
        return regSched

    def writeThkl(self, thklString):
        folder = self.settings.outputPath
        filename = self.path.stem
        with open((Path(folder)/filename).with_suffix(".fand"), 'w') as outf:
            outf.write(thklString)
        return

    def writeThks(self, *args, **kwargs):
        folder = self.settings.outputPath
        prev = set()
        for name, thk in zip(self.fileNames, self.thkFiles):
            if name in prev:
                continue
            else:
                output = (Path(folder)/name).with_suffix(".nack")
                output.parent.mkdir(parents=True, exist_ok=True)
                if self.settings.verbose:
                    self.settings.display("Decompiling %s" % (name))
                filedata = thk.decompile(*args, **kwargs)
                with open(output, 'w') as outf:
                    outf.write(filedata)
                prev.add(name)

    def setupStructures(self, entityMap=None, thkMap=None, functionResolver=None):
        if self.settings.outputPath is None:
            self.settings.outputPath = str(Path(self.path).parent)
        if self.settings.runCodeAnalysis:
            thkp = THKProject(self.path, settings=self.settings)
            if self.settings.statisticsOutputPath is None:
                root = self.path.parent
                self.settings.statisticsOutputPath = root
            base = self.path.stem + "_analysis.txt"
            with open(Path(self.settings.statisticsOutputPath)/base, "w") as inf:
                inf.write(str(thkp.dataSummary()))
        if entityMap is None:
            actionMap = loadActionMaps()
            entityMap = loadEntities(actionMap)
        if thkMap is None:
            thkMap = loadTHKMaps()
        self.entityMap = entityMap
        self.monster = self.consensusMonster(self.thkl)
        self.location = self.consensusLocation(self.thkl)
        self.folder = self.consensusFolder(self.thkl)
        self.scopeNamer = thkMap
        callResolver = self.buildCallResolver()
        scopeResolver = self.buildScopeResolver()
        registerScheduler = self.buildRegisterScheduler()
        if functionResolver is None:
            functionResolver = buildResolver()
        return callResolver, scopeResolver, registerScheduler

    def decompileProject(self, entityMap=None, thkMap=None, functionResolver=None):
        callResolver, scopeResolver, registerScheduler = self.setupStructures(
            entityMap, thkMap, functionResolver)
        self.setup = True
        thkl = self.decompile(entityMap, thkMap, functionResolver)
        self.writeThkl(thkl)
        self.writeThks(entityMap, callResolver, scopeResolver,
                       functionResolver, registerScheduler)
        self.setup = False
        return

    def writeFile(self, *args, **kwargs):
        self.decompileProject(*args, **kwargs)
