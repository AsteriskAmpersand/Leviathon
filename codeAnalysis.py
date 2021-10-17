# -*- coding: utf-8 -*-
"""
Created on Mon Sep 20 03:51:48 2021

@author: Asterisk
"""
from pathlib import Path
from collections import Counter
import regex

from thk import Thk
from thklist import ThkList

import networkx as nx
import actionEnum as ae
import thklSpecStr as thklStr
#Code Analysis
#Make a directed graph of the entire folder of thk
#Determine entry points from 00
#Report orphan nodes in 00
#Report which Int Registers are used by which modules
#Give global summary of Int Register availability
#Give per file summary of Int Register Usage (Checks X, Sets Y)
#Give per file summary of actions used on the file and on all of the calls it has access to

#Parse into thk into SNack
#Parse from SNack into thk

implementationExtension = ".nack"
headerExtension = ".fand"

class RawParser():
    def parseStream(self,data):
        self.path = Path("")
        rawstr = self.rawStructure.parse_stream(data)
        self.parse(rawstr)
    def parseFile(self,data):
        self.path = Path(data)
        rawstr = self.rawStructure.parse_file(data)
        self.parse(rawstr)

class MissingGlobalFunction(Exception):
    pass

class THKNode():
    def __init__(self,ix,node):
        self.node = node
        self.index = ix
        self.marked = False
    def __hash__(self):
        return hash(self.index)
    def targets(self,parentIndex,globaFile = None):
        targets = []
        for segment in self.node.segments:
            if segment.extRefThkID != -1 and globaFile is None:
                raise MissingGlobalFunction("Missing Global Node and passed external reference with ID %03d in THK_%02d"%(self.index,parentIndex))
            if segment.extRefThkID != -1:
                targets.append((globaFile.index,globaFile.find(segment.extRefNodeID)))
            if segment.localRefNodeID != -1:
                targets.append((parentIndex,segment.localRefNodeID))
        return targets
    def empty(self):
        return len(self.node.segments)==1#(self.node.segments[0].nodeEndingData // 10000) > 0
    def getRegisterUsage(self):
        registers = set()
        for segment in self.node.segments:
            if 0x80<=segment.functionType<=0xA7:
                if segment.functionType <= 0x93:
                    getset = "Set"
                    offset = 0x80
                else:
                    getset = "Get"
                    offset = 0x94
                regvar = chr(ord('A') + segment.functionType-offset)
                registers.add((regvar,getset))
        return registers
    def getActions(self):
        actions = set()
        for segment in self.node.segments:
            if segment.actionID > 0:
                actions.add(segment.actionID)
        return actions
    def getID(self):
        return self.node.id
    
class THKFile(RawParser):
    rawStructure = Thk
    def __init__(self,index=0,metaHash=0,data = None,fullpath = None):
        self.populated = False
        self.thk = None
        self.nodes = []
        self.path = ""
        self.void = True
        if fullpath is not None:
            self.void = False
            if fullpath == "":
                self.void = True
            elif type(fullpath) is str or type(fullpath) is type(Path()):
                if Path(fullpath).exists() and fullpath:
                    self.parseFile(fullpath)
                    self.path = data
                else:
                    self.path = data
            else:
                self.parseStream(data)
        self.index = index
        self.metaHash = metaHash
        self.cache_trace = None
    def clearMarks(self):
        for node in self.nodes:
            node.marked = False
    def parse(self,thk):
        self.populated = True
        self.thk = thk
        self.nodes = [THKNode(ix,node) for ix,node in enumerate(thk.nodeList)]
    def find(self,id):
        for node in self.nodes:
            if node.getID() == id:
                return node.index
        return -1*id
        #raise KeyError("ID %d missing from THK %d"%(id,self.index))
    def missing(self):
        return self.populated
    def trace(self,globaFile = None):
        if self.cache_trace: return self.cache_trace
        self.cache_trace = nx.DiGraph()
        for node in self.nodes:
            for source,target in node.targets(self.index,globaFile):
                self.cache_trace.add_edge((self.index,node.index),(source,target))
        return self.cache_trace
    def getActions(self,index = None):
        if index is None:
            usage = set()
            for node in self.nodes:
                usage = usage.union(self.getActions(node.index))
            return usage
        else:
            if index < 0:
                print("Invalid Index %d Used to Access Global THK"%abs(index))
                return set()
            return self.nodes[index].getActions()
    def getRegisterUsage(self,index = None):
        if index is None:
            usage = set()
            for node in self.nodes:
                usage = usage.union(self.getRegisterUsage(node.index))
            return usage
        else:
            if index < 0:
                print("Invalid Index %d Used to Access Global THK"%abs(index))
                return set()
            return self.nodes[index].getRegisterUsage()
    
                
def indices(lst, element):
    result = []
    offset = -1
    while True:
        try:
            offset = lst.index(element, offset+1)
        except ValueError:
            return result
        result.append(offset)

def rootMatch(parentPath,childPath):
    parentTrail = list(reversed(list(map(lambda x: x.stem,parentPath.parents))[:-1]))
    childTrail = list(reversed(list(map(lambda x: x.stem,childPath.parents))[:-1]))
    root = None
    if not childTrail: return ""
    nthLevel = childTrail[0]
    for index in indices(parentTrail,nthLevel):
        if parentTrail[index:index + len(childTrail)] == childTrail:
            root = list(parentPath.parents)[-index-1]
    return root

def cojoinedMatching(parentPath, childPath):
    root = rootMatch(parentPath,childPath)
    if root:
        return (root / childPath)
    return parentPath.parent
        
class THKSummary():
    #Make a directed graph of the entire folder of thk
    def __init__(self,trace,thklist):
        self.cache_trace = trace
        self.thklist = thklist
        self.actionMapper = None
        self.fileMapper = None
        self.result_cache = [None,None,None]
    def getConnectedNodes(self,file,globallyVisited):
        visited = set([0])
        try:
            connected = nx.dfs_postorder_nodes(self.cache_trace,source=(file.index,0))
            for (fileIx,nodeIx) in connected:
                if fileIx == file.index:
                    visited.add(nodeIx)
                else:
                    globallyVisited.add(nodeIx)
        except KeyError:
            return set()            
        return visited
    def orphans(self):
        #Determine entry points from 00
        #Report orphan nodes in 00
        if self.result_cache[0] is not None:
            return self.result_cache[0]
        globallyVisited = set()
        orphans = {}        
        for file in self.thklist.thkl:
            if file.index == 55:
                continue            
            visited = self.getConnectedNodes(file,globallyVisited)
            orphans[file.index] = set([node.index for node in file.nodes if not node.empty() and node.index not in visited])
        orphans[55] = set([node.index for node in self.thklist.thkl[55].nodes if not node.empty() and node not in globallyVisited])
        self.result_cache[0] = orphans
        return orphans
    def registerUsage(self):
        #Report which Int Registers are used by which modules
        #Give global summary of Int Register availability
        #Give per file summary of Int Register Usage (Checks X, Sets Y)
        if self.result_cache[1] is not None:
            return self.result_cache[1]
        globalFile = self.thklist.thkl[55]
        globalUsage = set()
        registerUsage = {}
        for file in self.thklist.thkl:
            if file.index == 55:
                continue
            usage = set()
            localGlobal = set()
            visited = self.getConnectedNodes(file,localGlobal)
            for index in visited:
                usage = usage.union(file.getRegisterUsage(index))
            for index in localGlobal:
                usage = usage.union(globalFile.getRegisterUsage(index))
            globalUsage = globalUsage.union(usage)
            registerUsage[file.index] = usage
        registerUsage[55] = globalUsage
        self.result_cache[1] = registerUsage
        return registerUsage            
    def actionUsage(self):
        #Give per file summary of actions used on the file and on all of the calls it has access to
        if self.result_cache[2] is not None:
            return self.result_cache[2]
        globalFile = self.thklist.thkl[55]
        globalUsage = set()
        actionUsage = {}
        for file in self.thklist.thkl:
            if file.index == 55:
                continue
            usage = set()
            localGlobal = set()
            visited = self.getConnectedNodes(file,localGlobal)
            for index in visited:
                usage = usage.union(file.getActions(index))
            for index in localGlobal:
                usage = usage.union(globalFile.getActions(index))
            globalUsage = globalUsage.union(usage)
            actionUsage[file.index] = usage
        actionUsage[55] = globalUsage
        self.result_cache[2] = actionUsage
        return actionUsage
    def resolveFile(self,fileIndex):
        if self.fileMapper:
            if fileIndex in self.fileMapper:
                return self.fileMapper[fileIndex]
        return "THK_" + "%02d"%(fileIndex)
    def resolveAction(self,actionID):
        if self.actionMapper:
            if actionID in self.actionMapper:
                return self.actionMapper[actionID]
        return "ACTION_"+"%03d"%(actionID)
    def reprRegisters(self,usage):
        registers = {}
        for reg,getset in sorted(usage):
            if reg in registers:
                registers[reg] = "%s: (Get,Set)"%reg
            else:
                registers[reg] = "%s: (%s)"%(reg,getset)
        return ''.join(["\t%s\n"%string for string in sorted(registers.values())])
    def reprActions(self,actionsUsed):
        return ''.join(["\t[%d] %s\n"%(ix,name) for ix,name in zip(sorted(actionsUsed),map(self.resolveAction,sorted(actionsUsed)))])
    sep = "="*20
    ssep = "-"*16+"\n"
    secSep = lambda self,x : "\n%s\n%s\n%s\n"%("="*20,x,"="*20)
    def summariseOrphans(self):
        orphans = self.orphans()
        result = ""
        result += self.secSep("Orphan Nodes")
        for file,fileOrphans in orphans.items():
            if fileOrphans:
                result += "%s: %s\n"%(self.resolveFile(file),', '.join(map(lambda x: "%02d"%x,fileOrphans)))
                result += self.ssep
        return result
    def summariseRegisters(self):
        registers = self.registerUsage()
        result = ""
        result += self.secSep("Register Usage")
        for file,registersUsed in registers.items():
            if registersUsed:
                result += "%s:\n"%(self.resolveFile(file))
                result += self.reprRegisters(registersUsed)
                result += self.ssep
        return result
    def summariseActions(self):
        actions = self.actionUsage()
        result = ""
        result += self.secSep("Action Usage")
        for file,actionsUsed in actions.items():
            if actionsUsed:
                result += "%s:\n"%(self.resolveFile(file))
                result += self.reprActions(actionsUsed)
                result += self.ssep   
        return result
    def __repr__(self):
        result = ""
        result += self.summariseOrphans()
        result += self.summariseRegisters()
        result += self.summariseActions()
        return result
        
defaultEnums = ae.DefaultDataEnum()

class THKProject(RawParser):
    rawStructure = ThkList
    def __init__(self,data = None,dataEnums = defaultEnums):
        self.cache_trace = None
        self.path = None
        self.type = None
        self.monster = None
        self.subspecties = None
        self.enums = dataEnums
        if data is not None:
            if type(data) is str or type(data) is type(Path()):
                self.parseFile(data)
                self.parsePath(data)
            else:
                self.parseStream(data)
    def parsePath(self,path):
        parsed = Path(path)
        emFormat = regex.compile(r".*em([0-9]{3})[\\/]([0-9]{2})[\\/].*")
        match = emFormat.match(str(path))
        if match:
            mon,sub = match.groups()
            self.subspecies = int(sub)
            self.monster = int (mon)
            self.type = "em"            
        emsFormat = regex.compile(r".*ems([0-9]{3})[\\/]([0-9]{2})[\\/].*")
        match = emsFormat.match(str(path))
        if match:
            mon,sub = match.groups()
            self.subspecies = int(sub)
            self.monster = int (mon)
            self.type = "ems"            
        otFormat = regex.compile(r".*otomo/common/data/.*")
        match = otFormat.match(str(path))
        if match:
            self.subspecies = 0
            self.monster = 0
            self.type = "otomo"
                                  
    def parse(self,thkl):
        self.thkl = [self.thkPathParse(ix,e.path+".thk" if e.path else "",d) for ix,(e,d) in enumerate(zip(thkl.entries,thkl.data))]
    def thkPathParse(self,ix,thkpath,d):
        if not thkpath:
            return THKFile(ix,d)
        matchedthkpath = Path(thkpath)
        matchedthkpath = cojoinedMatching(self.path,matchedthkpath)
        return THKFile(ix,d,thkpath,matchedthkpath)
    def traceGraph(self):
        if self.cache_trace is not None:
            return self.cache_trace
        bg = self.thkl[55].trace(self.thkl[55])
        for ix,file in enumerate(self.thkl):
            if file.index != 55:
                bg = nx.compose(bg,file.trace(self.thkl[55]))
        self.cache_trace = bg
        return self.cache_trace
    def dataSummary(self):        
        if self.cache_trace is None:
            self.traceGraph()
        summary = THKSummary(self.cache_trace,self)
        if self.monster is not None and self.type == "em":
            summary.actionMapper = ae.loadActionMaps()[(self.monster,self.subspecies)][1]
        summary.fileMapper = ae.loadTHKMaps().thkToModule
        return summary
    def resolveEntity(self):
        self.entity = None
        if (self.type,self.monster,self.subspecies) in self.enums.entityMap:
            self.entity = self.enums.entityMap[(self.type,self.monster,self.subspecies)]        
    def decompileLocation(self):
        entity = None
        if self.entity is not None:
            entity = self.entity.name
        if self.relativePath():
            location = self.relativePath()
        else:
            location = self.path
        return location,entity
    def decompile(self,actionEnum = ae):
        self.resolveEntity()
        location = self.decompileLocation()
        functions = [function for function in self.thkl if not function.void]
        count = len(self.thkl)
        return self.output(location,functions,count)
    def decompileFile(self,outputpath = None,actionEnum = ae):
        if outputpath is None:
            outputpath = self.path.with_suffix(headerExtension)
        output = self.decompile(ae)
        with open(outputpath,"w") as outf:
            outf.write(output)
    def relativePath(self):
        pool = [rootMatch(self.path,Path(func.path)) for func in self.thkl if func.path]
        rank = Counter(pool)
        options = sorted(rank,key = lambda x: rank[x], reverse = True)
        if rank[options[0]] > 1:
            return options[0]
        else:
            return self.path
    def output(self,location,functions,count):
        outputStr = ""
        #TODO relative path to chunk as path
        #Done actually also deal with un-renamed functions as .nack if they CAN be decompiled
        #Iterate over all files to get consensus of relative path
        #Iterate over all files to get consensus of monster entity
        
        outputStr += thklStr.location_str%location + "\n"
        for function in functions:
            path = '"%s"'%function.path
            index = "Thk_%02d"%function.index
            if function.populated:
                path = '".\\' + index + implementationExtension + '"'
            if self.entity:
                if function.index in self.enums.moduleInfo(self.type):
                    index = self.enums.moduleInfo(self.type)[function.index]
                    if function.populated:
                        path = '".\\' + index + implementationExtension + '"'
            outputStr += thklStr.function_str%(index,path,function.metaHash) + "\n"
        outputStr += thklStr.length_str%count + "\n"
        return outputStr

class THKParser():
    def __init__(self, data = None):
        self.type = None
        if type(data) is str or type(data) is type(Path()):
            thkpath = Path(data)
            if thkpath.is_dir():
                self.type = "Dir"
                self.directoryAnalysis(thkpath)
                #self.directoryAnalysis(thkpath)
            else:
                self.type = "File"
                self.fileAnalysis(thkpath)
    def codeAnalysis(self,file):
        pass
    def directoryAnalysis(self,folder):
        for header in folder.rglob("*.thklist"):
            project = THKProject(header)
            summary = project.dataSummary()
            print(summary)

#for thklist in Path(r"D:\Games SSD\MHW\chunk\em").rglob("*.thklst"):
#    try:
#        thkp = THKProject(thklist)
#        thkp.dataSummary()
#    except Exception as e:
#        print(thklist)
#        print(e)
        
#print(thkp.dataSummary())
if __name__ in "__main__":
    thkp = THKProject(r"D:\Games SSD\MHW\chunk\em\em108\00\data\em108.thklst")
    print(thkp.dataSummary())
    thkp.decompileFile(r"D:\Games SSD\MHW-AI-Analysis\em108.fand")