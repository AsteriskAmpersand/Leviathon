# -*- coding: utf-8 -*-
"""
Created on Thu Dec  9 00:02:23 2021

@author: Asterisk
"""
from pathlib import Path
from common.thklist import ThkList
from common.thk import Thk, Segment


class Index():
    def __init__(self):
        self.i = 0


def depthCalc(segment):
    if segment.branchingControl == 0x2:
        return 1
    if segment.branchingControl == 0x8:
        return -1
    if segment.endRandom == 0x40:
        return 1
    if segment.endRandom == 0x80:
        return -1
    return 0


irrelevantFields = {"localRefNodeID", "extRefNodeID",
                    "padding", "monsterID", "isPalico",
                    "functionType", "nodeEndingData"}
relevantFields = [field.name for field in Segment.subcons
                  if field.name not in irrelevantFields]


def nonEmptyNodes(segment):
    calls = {"localRefNodeID", "extRefNodeID", "extRefThkID"}
    for field in relevantFields:
        if field not in calls:
            if getattr(segment,field) != 0:
                return True
    for field in calls:
        if getattr(segment,field) != -1:
            return True
    if segment.functionType > 2:
        return True
    return False

def enumerateTHK(index, table, filepath, globalTable={}):
    thk = Thk.parse_file(filepath.replace("/", "\\"))
    nodeIds = {}
    nodeIxs = {}
    for ix, node in enumerate(thk.nodeList):
        node.state = index.i
        nodeIds[node.id] = node.state
        nodeIxs[ix] = node.state
        depth = 0
        node.segments = list(filter(nonEmptyNodes, node.segments))
        for jx, segment in enumerate(node.segments):
            # branchingControl 0x2 0x8 chance  0x40 0x80
            depth += depthCalc(segment)
            segment.state = index.i
            table[index.i] = segment
            index.i += 1
            segment.nextState = index.i
            segment.path = filepath
            segment.depth = depth
            segment.node = ix
            segment.index = jx
        segment.nextState = None
    for node in thk.nodeList:
        for segment in node.segments:
            alt = None
            if segment.extRefNodeID != -1:
                if segment.extRefNodeID in globalTable:
                    alt = globalTable[segment.extRefNodeID]
            elif segment.localRefNodeID != -1:
                if segment.localRefNodeID in nodeIxs:
                    alt = nodeIxs[segment.localRefNodeID]
            segment.altState = alt
            segment.step = NextObj(
                segment.flowControl != 0 and not segment.depth, segment.nextState, alt)
    return nodeIds


class Table(dict):
    pass


def analyzeTHKL(root, file):
    i = Index()
    startingIndices = [0]
    table = Table()
    table.name = file
    thkl = ThkList.parse_file(file)
    globalThk = {}
    if len(thkl.entries) > 55:
        entry = thkl.entries[55]
        if entry.path:
            globalThk = enumerateTHK(
                i, table, root+"/"+entry.path+".thk", globalThk)
    for thkix, entry in enumerate(thkl.entries):
        if entry.path and thkix != 55:
            startingIndices.append(i.i)
            enumerateTHK(i, table, root+"/"+entry.path+".thk", globalThk)
    return table, startingIndices


class DesynchronizationError(Exception):
    pass


class Terminated(Exception):
    pass


def displaySegment(segment):
    result = "<%s>"
    results = []
    for field in relevantFields:
        if field != "extRefThkID":
            if getattr(segment, field) != 0:
                results.append("%s=%s" % (field, str(getattr(segment, field))))
    field = "functionType"
    if getattr(segment, field) not in [0, 2]:
        results.append("%s=%X" % (field, getattr(segment, field)))
    if segment.localRefNodeID != -1:
        if segment.altState:
            results.append("local_call=%d" % segment.altState)
    if segment.extRefNodeID != -1:
        if segment.altState:
            results.append("global_call=%d" % segment.altState)
    results.append("thk=%s" % Path(segment.path).stem)
    results.append("node=%d" % segment.node)
    return "<%s>" % (",".join(results))


class ParallelControler():
    def __init__(self, programs, output=print):
        self.programs = programs
        self.output = output

    def compare(self, segments):
        segment0 = segments[0]
        register0 = segment0.functionType in range(0x80, 0xac)
        errors = []
        for segment in segments[1:]:
            additional = ["functionType"]\
                if segment.functionType not in [0, 2, *range(0x80, 0xac)]\
                else []
            for field in relevantFields + additional:
                f0 = getattr(segment0, field)
                f1 = getattr(segment, field)
                if not f0 == f1:
                    errors.append((field, f0, f1,
                                   Path(
                                       segment0.path).stem, segment0.node, segment0.index,
                                   Path(segment.path).stem, segment.node, segment.index))
            register = segment.functionType in range(0x80, 0xac)
            if register != register0:
                errors.append(("functionType", Path(segment0.path).stem,
                               segment0.node, Path(segment.path).stem, segment.node))
        if errors:
            raise DesynchronizationError('\n'.join(map(str, errors)))
        self.output(displaySegment(segment0))
        return

    def step(self):
        segments = []
        validprograms = []
        for program in self.programs:
            try:
                segment = program.step()
                segments.append(segment)
                validprograms.append(program)
            except:
                pass
        if validprograms and len(segments) != len(self.programs):
            sg = '\n'.join(map(lambda x: x.path, validprograms))
            raise DesynchronizationError(
                "Execution Terminated only on some programs:"+sg)
        if not validprograms:
            raise Terminated()
        self.compare(segments)

    def run(self):
        for stateSets in zip(*map(lambda x: x.startingStates, self.programs)):
            for state, prog in zip(stateSets, self.programs):
                prog.setState(state)
            self.output(prog.currentPath())
            while True:
                try:
                    self.step()
                except Terminated:
                    break


class NextObj():
    def __init__(self, reset, state, alt):
        self.reset = reset
        self.state = alt if alt is not None else state
        self.alt = state if alt is not None else None
        self.end = state is None and alt is None


class ExecutionEnded(Exception):
    pass


class ThreadController():
    def __init__(self, startingstates, table):
        self.startingStates = startingstates
        self.state = startingstates[0]
        self.history = set()
        self.rsi = []
        self.table = table
        self.path = table.name

    def setState(self, ix):
        self.state = ix

    def currentPath(self):
        return self.table[self.state].path

    def step(self):
        segment = self.table[self.state]
        nextObj = segment.step
        if nextObj.end:
            raise ExecutionEnded
        if nextObj.alt is not None:
            self.rsi.append(nextObj.alt)
        if nextObj.reset:
            if self.rsi:
                self.state = self.rsi.pop()
            else:
                raise ExecutionEnded
        else:
            self.state = nextObj.state
        while self.state in self.history and self.rsi:
            self.state = self.rsi.pop()
        if self.state in self.history:
            raise ExecutionEnded
        self.history.add(self.state)
        return self.table[self.state]


def loadFile(root, thklpath):
    table, ixes = analyzeTHKL(root, thklpath)
    return ThreadController(ixes, table)


def comparePrograms(programs, output=print):
    parallelList = []
    for root, thklpath in programs:
        parallelList.append(loadFile(root, thklpath))
    ParallelControler(parallelList, output)


root = r"D:\Games SSD\MHW\chunk"
thklpath = r"D:\Games SSD\MHW\chunk\em\em001\00\data\em001.thklst"
table = loadFile(root, thklpath)

root2 = r"D:\Games SSD\MHW-AI-Analysis\Leviathon\tests\ingameOutputs"
thklpath2 = r"D:\Games SSD\MHW-AI-Analysis\Leviathon\tests\ingameOutputs\em\em001\00\data\em001.thklst"
table2 = loadFile(root2, thklpath2)
pc = ParallelControler([table, table2])

pc.run()
