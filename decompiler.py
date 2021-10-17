# -*- coding: utf-8 -*-
"""
Created on Mon Oct 11 18:25:32 2021

@author: Asterisk
"""
from pathlib import Path
from collections import Counter

from thk import Thk, Node, Segment, Header 
from thklist import ThkList
from fexLayer import buildResolver
from actionEnum import loadActionMaps,loadTHKMaps
from monsterEnum import loadEntities
from codeAnalysis import THKProject, rootMatch, cojoinedMatching
import keywords as key
import thklSpecStr as thklSpec
#Decompilation

#Load THKL
#Load THKs
#Perform Local Node Naming and Enumeration
#Map each file naming and enumeration (Scoped name on import, THK > THKL > THKRef (so scope is named after the THKL label for the file)
#Resolve Actions Locally for each file (Add Comments if a call is void) (Allow the decompiler to use customized mappings)
#Resolve Calls to Scope + Name or Name if local (Add Comments if a call is void) (Is it just passing a dict with Index -> Scope Name, Node# -> Function Name)
#Resolve Function Checks through the Specification  (from  the FExtY file)



class DecompilerSettings():
    def __init__(self):
        self.keepVoid = False
        self.keepLast = False
        self.forceIndex = False
        self.forceId = True
        self.listCrossreferences = False
        
        self.raiseInvalidReference = False
        self.suppressWarnings = False
        self.keepRegisters = False
        self.functionAsThkName = False
    
        self.runCodeAnalysis = False
        
        self.outputPath = None
        self.statisticsOutputPath = None

class CompilerSettings():
    pass

class TranspilerSettings():
    def __init__(self):
        self.decompiler = DecompilerSettings()
        self.compiler = CompilerSettings()

class Transpiler():
    def __init__(self,settings = None):
        if settings is None:
            settings = TranspilerSettings()
        self.settings = settings
          
class THKLEntry():
    def __init__(self,index,metadata,partialPath=None,fullPath=None):
        self.valid = partialPath is not None
        self.index = index
        self.metadata = metadata
        self.partialPath = partialPath
        self.fullPath = fullPath
    
class THKLTranspiler(Transpiler):
    #functionResolver = buildResolver(r'default.fexty')
    def __init__(self,settings = None):
        super().__init__(settings)
        self.setup = False
    def consensusLocation(self,thklist):
        roots = Counter()
        for thkp in thklist:
            if thkp.valid:
                match = rootMatch(Path(self.path),Path(thkp.partialPath))
                if match:
                    roots[match] += 1
        if roots:
            return next(iter(roots.most_common()))[0]
        else:
            return self.path.parent
    def consensusFolder(self,thklist):
        roots = Counter()
        for thkp in thklist:
            if thkp.valid:
                for p in Path(thkp.partialPath).parents:
                    roots[p] += 1
        if roots:
            return str(next(iter(sorted(roots.items(),key = lambda x: (-x[1], -len(str(x[0]))))))[0])
        else:
            return ""
    def consensusMonster(self,thklist):
        monster = Counter()
        for thkp in thklist:
            if thkp.valid:
                if Path(thkp.fullPath).exists():
                    thkh = Header.parse_file(thkp.fullPath)
                    monster[(thkh.monsterID,thkh.isPalico)] += 1
        if monster:
            monId,palico = next(iter(monster.most_common()))[0]
            if not palico:
                return self.entityMap.getName(monId)
            else:
                return "Palico"
        else:
            return None
    def read(self,path):
        self.path = Path(path)
        thkl = ThkList.parse_file(path)
        self.thkl = [self.thkPathParse(ix,e.path+".thk" if e.path else "",d) for ix,(e,d) in enumerate(zip(thkl.entries,thkl.data))]
        self.thkFiles = [THKTranspiler(self.settings).read(thk.partialPath,thk.fullPath,thk.index) for thk in self.thkl if thk.valid]
        return self
    def thkPathParse(self,ix,thkpath,d):
        if not thkpath:
            return THKLEntry(ix,d)
        matchedthkpath = Path(thkpath)
        matchedthkpath = cojoinedMatching(self.path,matchedthkpath)
        return THKLEntry(ix,d,thkpath,matchedthkpath)
    def decompile(self,entityMap=None,thkMap=None,functionResolver = None):
        if not self.setup:
            self.setupStructures(entityMap,thkMap,functionResolver)
        result = ""
        if self.location:
            result += (thklSpec.chunk_str%self.location) + "\n"
        if self.folder:
            result += (thklSpec.filepath_str%self.folder) + "\n"
        if self.monster:
            result += thklSpec.monster_str % self.monster + "\n"
        if result: result+="\n"
        result += self.registerScheduler.declarations(self.settings.decompiler.keepRegisters)
        self.fileNames = []
        for thk in self.thkl:
            if thk.valid:
                if self.settings.decompiler.functionAsThkName:
                    partial = Path(thkMap.resolve(thk.index).lower()+".nack")
                else:
                    try:
                        partial = Path(thk.partialPath).relative_to(self.folder).with_suffix(".nack")
                    except:
                        partial = Path(thk.partialPath).with_suffix(".nack")
                self.fileNames.append(partial)
                result += thklSpec.function_str % (thkMap.resolve(thk.index), partial, thk.metadata) + "\n"
        result += thklSpec.length_str%len(self.thkl)
        return result
    def buildCallResolver(self):
        callResolver = CallResolver()
        for thk in self.thkFiles:
            callResolver[thk.index] = thk.nodeListing
            #print(thk.nodeListing.rawIndexToNode.keys())
            #raise
        self.callResolver = callResolver
        return callResolver
    def buildScopeResolver(self):
        scopeResolver = ScopeResolver()
        for thk in self.thkFiles:
            scopeResolver.addEntry(thk.index,self.scopeNamer.resolve(thk.index))
        self.scopeResolver = scopeResolver
        return scopeResolver
    def buildRegisterScheduler(self):
        registers = set()
        for thk in self.thkFiles:
            registers = registers.union(thk.registerUsage())
        regSched = RegisterScheduler()
        for ix,register in enumerate(sorted(registers)):
            regSched.label(register,"RegisterVar%d"%ix)
        self.registerScheduler = regSched
        return regSched
    def writeThkl(self,thklString):
        folder = self.settings.decompiler.outputPath
        filename = self.path.stem
        with open((Path(folder)/filename).with_suffix(".fand"),'w') as outf:
            outf.write(thklString)
        return
    def writeThks(self,*args,**kwargs):
        folder = self.settings.decompiler.outputPath
        for name,thk in zip(self.fileNames,self.thkFiles):
            filedata = thk.decompile(*args,**kwargs)
            with open((Path(folder)/name).with_suffix(".nack"),'w') as outf:
                outf.write(filedata)
    def setupStructures(self,entityMap=None,thkMap=None,functionResolver=None):
        if self.settings.decompiler.outputPath is None:
            self.settings.decompiler.outputPath = str(Path(self.path).parent)
        if self.settings.decompiler.runCodeAnalysis or True:
            thkp = THKProject(self.path)
            if self.settings.decompiler.statisticsOutputPath is None:
                root = self.path.parent
                self.settings.decompiler.statisticsOutputPath = root
            base = self.path.stem + "_analysis.txt"
            with open(Path(self.settings.decompiler.statisticsOutputPath)/base,"w") as inf:
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
        callResolver = self.buildCallResolver() #TODO - Have to build it from the nodes -> THK index to node listing
        scopeResolver = self.buildScopeResolver()#TODO - Build from nodes
        registerScheduler = self.buildRegisterScheduler()#TODO - Have to build it gather the register usage and rename them based on compile settings, add register declaration to thkl
        if functionResolver is None:
            functionResolver = buildResolver()
        return callResolver,scopeResolver,registerScheduler
    def decompileProject(self,entityMap=None,thkMap=None,functionResolver=None):
        callResolver,scopeResolver,registerScheduler = self.setupStructures(entityMap,thkMap,functionResolver)
        self.setup = True
        thkl = self.decompile(entityMap,thkMap,functionResolver)
        self.writeThkl(thkl)
        self.writeThks(entityMap,callResolver,scopeResolver,functionResolver,registerScheduler)
        self.setup = False
        return
    def writeFile(self,*args,**kwargs):
        self.decompileProject(*args,**kwargs)

def checkEmptyFields(node):
    segment = node.segments[0]
    for field in Segment.subcons:
        name = field.name
        if name in ["padding","monsterID","isPalico","log"]:
            continue
        val = getattr(segment,name)
        if name in ["extRefThkID","extRefNodeID","localRefNodeID"]:
            if val != -1:
                #print("REF")
                return False
        elif name in ["endRandom"]:
            if val not in [0,1]:
                #print("ENDRANDOM")
                return False
        elif name in ["nodeEndingData"]:
            if val // 10000 not in [0,1]:
                #print("ENDIGNDATA")
                return False
        else:
            if val != 0:
                print(name)
                return False
    return True

def checkEmptyNode(node):
    if node.id == 0:
        if len(node.segments) == 1:
            if checkEmptyFields(node):
                return False
    return True

class NodeListing():
    def __init__(self):
        self.idToNode = {}
        self.indexToNode = {}
        self.rawIndexToNode = {}
        self.nodeToIndex = {}
        self.nodeToId = {}
    def conditionalAdd(self,dic,key,val):
        if key in dic and key != 0:
            raise KeyError("Existing entry on node manifest: %s (%s <> %s)"%(str(key), val, dic[key].getName()))
        dic[key] = val
    def add(self,node,index):
        self.conditionalAdd(self.idToNode,node.id,node)
        self.conditionalAdd(self.indexToNode,index,node)
        self.conditionalAdd(self.rawIndexToNode,node.index,node)
        for name in node.names:
            self.conditionalAdd(self.nodeToIndex,name,index)
            self.conditionalAdd(self.nodeToId,name,node.id)
    
class MissingCallID(Exception):
    def __init__(self, scope, iD):
        self.scopeIndex = scope
        self.id = iD
       
class CallResolver(dict):
    def __init__(self,premade = None):
        self.localIndex = None
        if premade is not None:
            self.update(premade)
    def setLocal(self,index):
        self.localIndex = index
    @classmethod
    def defaultCall(cls,callIndex):
        return key.CALL + "#%03d"%callIndex
    def resolve(self,segment):
        segment.log("extRefThkID")
        segment.log("extRefNodeID")
        segment.log("localRefNodeID")
        if segment.extRefThkID != -1:
            scope = segment.extRefThkID
            index = segment.extRefNodeID
            if scope in self:
                if index in self[scope].idToNode:
                    return scope,self[scope].idToNode[index].names[0]
                else:
                    raise MissingCallID(scope,index)
            else:
                return scope,self.defaultCall(index)
        elif segment.localRefNodeID != -1:
            scope = self.localIndex
            index = segment.localRefNodeID
            if scope in self:
                if index in self[scope].rawIndexToNode:
                    return "local",self[scope].rawIndexToNode[index].names[0]
                else:
                    raise MissingCallID("local",index)
            else:
                return None,self.defaultCall(index)
        else:
            return None,""

class RegisterScheduler():
    def __init__(self):
        self.mappings = {}
    def defaultName(self,registerIndex):
        return "$"+chr(ord("A")+registerIndex)
    def addEntries(self,entries):
        for entry in entries:
            self.entries[entry] = self.defaultName(entry)
    def label(self,index,name):
        self.mappings[index] = name
    def resolve(self,registerIndex):
        if registerIndex in self.mappings:
            return self.mappings[registerIndex]
        else:
            return self.defaultName(registerIndex) 
    def declarations(self,keep = False):
        declarations = []
        for entry,name in self.mappings.items():
            letter = self.defaultName(entry)
            if not keep:
                declarations.append(thklSpec.register_anon_str%(name))
            else:
                declarations.append(thklSpec.register_str%(name,letter))
        return '\n'.join(declarations)+"\n\n" if declarations else ""
class ScopeResolver():
    def __init__(self):
        self.importList = set()
        self.scopeMapping = {55:"Global"}
        self.inverseScopeMapping = {"Global":55}
    def addEntry(self,index,name):
        self.scopeMapping[index] = name
        self.inverseScopeMapping[name] = index
    def startContext(self):
        self.importList = set()
    def imports(self):
        return self.importList
    def defaultContext(self,index):
        return "Thk_%02d"%index
    def resolve(self,contextIndex):
        if contextIndex not in self.scopeMapping:
            scopeTarget = self.defaultContext(contextIndex)
            scopeValue = contextIndex
        else:
            scopeTarget = self.scopeMapping[contextIndex]
            scopeValue = scopeTarget
        self.importList.add((scopeValue,scopeTarget))
        return scopeTarget

class THKTranspiler(Transpiler):
    #check references on nodes to see if there's any missing index, if there is
    #need to re-enable those function on fixed indices
    
    #need to build scope resolution operator
    #it needs to log all of the scopes checked on it to add them 
    #to the declaration at the top
     
    #actionResolver = loadActionMaps
    #entityResolver = loadEntities(actionResolver)
    def __init__(self,settings = None):
        super().__init__(settings)
        self.localPath = ""
        self.globalPath = ""
        self.index = None
        self.imports = []
        self.actionLibrary = []
        self.crossreference = []
    def read(self,local,glb=None,index=None):
        if glb is None:
            glb = local
            index = 0
        self.localPath = local
        self.globalPath = glb
        self.index = index
        thk = Thk.parse_file(self.globalPath)
        self.nodes = [NodeTranspiler(ix,self.settings).read(node) for ix,node in enumerate(thk.nodeList)]
        self.monster = thk.header.monsterID
        self.labelNodes()
        return self
    def labelNodes(self):
        self.nodeListing = NodeListing()
        validNodes = []
        for node in self.nodes:
            valid = checkEmptyNode(node.node)
            if valid or self.settings.decompiler.keepVoid:
                if self.settings.decompiler.forceIndex: node.explicitPosition(True)
                if self.settings.decompiler.forceId: node.explicitId(True)
                node.label(len(validNodes))
                self.nodeListing.add(node,len(validNodes))
                validNodes.append(node)
        if not valid and self.settings.decompiler.keepLast:
            node.label(len(validNodes))
            node.explicitPosition(True)
            self.nodeListing.add(node,len(validNodes))
            validNodes.append(node)
        self.validNodes = validNodes
        return self.nodeListing
    def registerUsage(self):
        #if hasattr(self,"registers"):
        #    return self.registers
        segmentSet = set()
        for node in self.nodes:
            newRegs = set(sum(map(lambda x: x.registers,node.segments),[]))
            segmentSet = segmentSet.union(newRegs)
        self.registers = segmentSet
        return self.registers
    def createEmptyNodes(self,index,*args,**kwargs):
        return self.nodes[index[1]].decompile(*args,position = True,**kwargs)
    def generateHeader(self,entityResolver,scopeResolver):
        imports = scopeResolver.imports()
        header = ""
        if self.settings.decompiler.listCrossreferences:
            if self.crossreference:
                comments = ["// Xref: "]
                for scopeSource,node in sorted(self.crossreferences):
                    if len(comments[-1]) > 75:
                        comments.append("")
                    scope = "" if scopeSource == "local" else scopeSource + "."
                    comments[-1] += scope + node + ", "                    
        if self.monster in entityResolver:
            action = self.monsterName
            header += key.IMPORTACT + " %s as %s\n" % (action,action.lower())
        for importSource,importTarget in imports:
            header += key.IMPORTLIB + " %s as %s\n" % (str(importSource),str(importTarget))
        return header+"\n"
    def decompile(self,entityResolver = None,
                      callResolver = None,
                      scopeResolver = None,
                      functionResolver = None,
                      registerScheduler = None):
        if not hasattr(self,"nodeListing"): self.labelNodes
        if entityResolver is None:
            actionResolver = loadActionMaps()
            entityResolver = loadEntities(actionResolver)
        if callResolver is None:
            callResolver = CallResolver({55:NodeListing(), self.index : self.nodeListing})
        callResolver.setLocal(self.index)
        if registerScheduler is None:
            registerScheduler = RegisterScheduler()
        if functionResolver is None:
            functionResolver = buildResolver()
        if scopeResolver is None:
            scopeResolver = ScopeResolver()
        header = ""
        if self.monster in entityResolver:
            self.monsterName = entityResolver.getName(self.monster)
            entityResolver[self.monster].scopeName = self.monsterName.lower()
        else:
            self.monsterName = "monster"
        scopeResolver.startContext()
        missingIndices = []
        nodes = ""
        for node in self.validNodes:
            actionResolver = entityResolver[self.monster]
            #node.explicitPosition(True)
            #node.explicitId(False)
            nodes += node.decompile(actionResolver,callResolver,scopeResolver,functionResolver,registerScheduler)
            missingIndices += node.missingLocalReferences
        #for index in sorted(set(missingIndices)):
        for index in set(missingIndices):
            #print(index)
            nodes += self.createEmptyNodes(index,actionResolver,callResolver,scopeResolver,functionResolver,registerScheduler)
        return self.generateHeader(entityResolver,scopeResolver) + nodes
    def writeFile(self,*args,**kwargs):
        if self.settings.decompiler.outputPath is None:
            self.settings.decompiler.outputPath = str(Path(self.globalPath).parent)
        decompilation = self.decompile(*args,**kwargs)
        folder = self.settings.decompiler.outputPath
        name = Path(self.globalPath).stem
        with open((Path(folder)/name).with_suffix(".nack"),'w') as outf:
            outf.write(decompilation)
        

class NodeTranspiler(Transpiler):
    def __init__(self,index = None,settings = None):
        super().__init__(settings)
        self.names = []
        self.index = index
        self.indexOverride = False
        self.idOverride = False
    def read(self,node):
        self.node = node
        self.id = node.id
        self.index = node.index if hasattr(node,"index") else self.index
        self.segments = [SegmentTranspiler(self.settings).read(segment) for segment in self.node.segments]
        return self
    def label(self,index,name = ""):
        if name:
            self.names.append(name)
        else:
            self.names.append("node_%03d"%index)
    def explicitPosition(self,val):
        self.indexOverride = val
    def explicitId(self,val):
        self.idOverride = val
    def getName(self):
        return self.names[0]
    def headerText(self,position = False,showId = True):
        header = key.DEF + " "
        header += " & ".join(self.names)
        if showId and self.idOverride:
            header += " : " + str(self.id)
        if position or self.indexOverride:
            header += " @ %d"%self.index
        header += "\n"
        return header
    def decompile(self,*args,position = False,**kwargs):
        missingLocalReferences = []
        result = ""
        result += self.headerText(position)
        indentationDepth = 1
        for segment in self.segments:
            segmentString = segment.decompile(*args,**kwargs)
            indentationDepth -= segment.checkSubstraction()
            result += '\t'*indentationDepth + segmentString
            indentationDepth += segment.checkAddition()
            missingLocalReferences += segment.missingLocalReferences
        self.missingLocalReferences = missingLocalReferences
        return result+"\n"
    
def spaceIfOp(string):
    if not string:
        return string
    return string + " "

class SegmentTranspiler(Transpiler):
    def __init__(self,settings = None):
        super().__init__(settings)
        self.initMembers()
    def initMembers(self):
        self.addIndent = False
        self.removeIndent = False
        
        self.used = set()
        self.missingLocalReferences = []
        self.active = False
        self.flow = ""
        self.function = ""
        self.action = ""
        self.call = ""
        self.directive = ""
        self.meta = ""
        
        self.functionName = ""
        self.actionName = ""
        self.callName = ""
        self.comments = ""
        self.registers = []    
    def read(self,segment):
        self.segment = segment
        segment.log = self.log
        if 0x80 <= self.segment.functionType <= 0xa7:
            self.registers.append((self.segment.functionType - 0x80 )%20)
        return self
    def getActionParams(self,segment):
        i = 4
        field = lambda i: "actionUnkn%d"%i
        getField = lambda i: getattr(segment, field(i))
        while (i>=0 and getField(i)==0): i-=1
        params = [str(getField(j)) for j in range(i+1) if segment.log(field(j)) or True]
        return ','.join(params)
    def resolveActions(self,actionResolver):
        if self.segment.actionID != 0:
            self.log("actionID")
            self.actionName = actionResolver.resolveActionIndex(self.segment.actionID)
            self.actionParams = self.getActionParams(self.segment)
            self.action = key.DO_ACTION + " " + self.actionName + "(" + self.actionParams + ")"
        else:
            return None
    def resolveCalls(self,callResolver,scopeResolver):
        try:
            scope,callName = callResolver.resolve(self.segment)
        except MissingCallID as m:
            if m.scopeIndex == "local":
                self.missingLocalReferences.append((m.scopeIndex,m.id))
            else:
                if self.settings.decompiler.raiseInvalidReference:
                    raise
                if not self.settings.decompiler.suppressWarnings:
                    self.comments += "-THK_%02d is missing NodeID %03d. "%(m.scopeIndex,m.id)
            scope = m.scopeIndex
            callName = CallResolver.defaultCall(m.id)
        if scope == "local":
            self.callName = callName
            self.call = key.DO_CALL+" %s"%callName
        elif scope is not None:
            self.callName = callName
            self.call = key.DO_CALL+" %s.%s"%(scopeResolver.resolve(scope),callName)
    def resolveFunctions(self,functionResolver,registerScheduler):
        if self.segment.functionType not in [0,2]:
            if 0x80 <= self.segment.functionType <= 0xa7:
                registerIndex = ( self.segment.functionType - 0x80 ) % 20
                registerName = registerScheduler.resolve( registerIndex )
                self.functionName = functionResolver.registerResolve(self.segment,registerName)
                self.function = self.functionName
            else:
                self.functionName = functionResolver.resolve(self.segment)
                self.function = self.functionName
            return self.functionName
        return None
    def decompile(self,actionResolver,callResolver,scopeResolver,functionResolver,registerScheduler):
        self.checkFlow()
        self.resolveActions(actionResolver)
        self.resolveCalls(callResolver,scopeResolver)
        self.resolveFunctions(functionResolver,registerScheduler)
        self.checkDirective()
        self.checkMeta()
        if not any([self.flow,self.function,self.action,self.call]):
            if self.directive:
                self.directive = self.directive[3:]
        code = ''.join(map(spaceIfOp,[self.flow,self.function,self.action,self.call,self.directive,self.meta]))
        if code == "": code = "*&"
        if self.comments:
            code += "// " + self.comments
        return code + "\n"
    
    def checkActive(self,segment):
        #action call directive
        self.active |= segment.functionType > 2
        self.active |= segment.extRefThkID != -1 or segment.localRefNodeID != -1
        self.active |= segment.flowType != 0

    def checkFlow(self):
        self.checkConditional()
        self.checkTerminal()
        self.checkChance()
        self.checkEndNode()
    def checkEndNode(self):
        segment = self.segment
        if segment.endRandom == 1:
            self.flow = key.ENDF
            self.removeIndent = True
            self.log("nodeEndingData")
            self.log("endRandom")
            return True
        return False
    def checkChance(self):
        chanceIndent = 3
        segment = self.segment
        if segment.branchingControl == 0x1:
            if self.active:
                self.flow = key.ENDCW
                self.removeIndent = chanceIndent
                self.log("branchingControl")
            else:
                self.flow = key.ENDC
                self.removeIndent = chanceIndent
                self.log("branchingControl")
            return True
        if segment.endRandom in [0x40,0xC0,0x80]:
            if segment.endRandom == 0x40:
                self.flow = key.CHANCE+" (%d)" % segment.parameter1 
                self.addIndent = chanceIndent
            else:
                self.removeIndent = chanceIndent
                self.addIndent = chanceIndent
                self.flow = key.ELSEC+" (%d)" % segment.parameter1 
            self.log("endRandom").log("parameter1")
            return True
        return False
    def checkConditional(self):
        segment = self.segment
        if segment.branchingControl == 0x2:
            self.flow = key.IF
            self.addIndent = True
        elif segment.branchingControl == 0x4:
            if segment.functionType > 2:
                self.flow = key.ELIF
                self.removeIndent = True
                self.addIndent = True
            else:
                self.flow = key.ELSE
                self.removeIndent = True
                self.addIndent = True
        elif segment.branchingControl == 0x8:
            if self.active:
                self.flow = key.ENDIFW
                self.removeIndent = True
            else:
                self.flow = key.ENDIF
                self.removeIndent = True
        else:
            return False
        self.log("branchingControl")
        return True
    
    def checkTerminal(self):
        segment = self.segment
        if segment.branchingControl == 0x10:
            self.flow = key.ENDALL
            self.log("branchingControl")
            return True
        return False
    
    def checkDirective(self):
        segment = self.segment
        if segment.flowControl == 0x4:
            self.directive = key.DO_DIRECTIVE + " " + key.REPEAT
        elif segment.flowControl == 0x8:
            self.directive = key.DO_DIRECTIVE + " " + key.RETURN
        elif segment.flowControl == 0x80:
            self.directive = key.DO_DIRECTIVE + " " + key.RESET
        else:
            return False
        self.log("flowControl")
        return True

    def checkMeta (self):
        segment = self.segment
        meta = {}
        self.used.add("monsterID")
        self.used.add("isPalico")
        self.used.add("padding")
        for value in Segment.subcons:
            if value.name not in self.used:
                var = getattr(segment,value.name)
                if  var != 0:
                    if value.name == "functionType" and var == 2:
                        pass
                    elif value.name in ['extRefThkID', 'extRefNodeID', 'localRefNodeID']\
                                        and var == -1:
                        pass
                    else:
                        meta[value.name] = var
        if meta:
            self.meta = key.META + " " + ", ".join((key+":"+str(val) for key,val in meta.items()))
            
    def checkAddition(self):
        return self.addIndent
    def checkSubstraction(self):
        return self.removeIndent
    
    def log(self,varname):
        if varname in self.used:
            raise ValueError("Segment is using the same field (%s) more than once"%varname)
        self.used.add(varname)
        return self

if __name__ in "__main__":
    inputThk = 0
    chunk = r"D:\Games SSD\MHW\chunk"
    folder = r"\em\em001\00\data"
    file = folder + r"\em001_%02d.thk"%inputThk
    inputStr = chunk + file
    thkf = THKTranspiler()
    thkf.read(file,inputStr,inputThk)
    with open(inputStr.replace(".thk",".nack").replace(
            chunk+folder,r"C:\Users\Asterisk\Downloads"
            ),"w") as outf:
        outf.write(thkf.decompile())
    thkl = chunk + folder + r"\em001.thklst"
    ts = TranspilerSettings()
    ts.decompiler.outputPath = r"D:\Games SSD\MHW-AI-Analysis\RathianTest"
    ts.decompiler.statisticsOutputPath = r"D:\Games SSD\MHW-AI-Analysis\RathianTest"
    print(THKLTranspiler(ts).read(thkl).decompile())
    """
    with open(inputStr,"rb") as inthk:        
        thk.read("
        thk = Thk.parse_stream(inthk)
        resolver = buildResolver(r'default.fexty')
        for node in thk.nodeList:
            for segment in node.segments:
                tSeg = SegmentTranspiler()
                tSeg.read(segment)
                segfun = tSeg.resolveFunctions(resolver, RegisterScheduler())
                if segfun: print(segfun)
    """