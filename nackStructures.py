# -*- coding: utf-8 -*-
"""
Created on Fri Oct 29 12:23:10 2021

@author: Asterisk
"""
from collections import defaultdict
from pathlib import Path

from signatures import compilerSignature
from compilerErrors import SemanticError
from errorHandler import ErrorManaged
from actionEnum import parseActionFile
from compilerUtils import Autonumber
import thk
import nackParse as np


def copy(self):
    if type(self) is int:
        return self
    elif type(self) is str:
        return self
    elif type(self) is type(None):
        return self
    elif type(self) is bool:
        return self
    elif type(self) is dict:
        return {copy(key):copy(val) for key,val in self.items()}
    else:
        return self.copy().copyMetadataFrom(self)

class NackFile(ErrorManaged):
    tag = "Nack File"
    subfields = ["nodes","scopeNames","actionScopeNames"]
    def __init__(self,parent = None):
        self.scopeNames = {"Local":ScopeTarget(Identifier("Local"),"local"),
                           "Terminal_Local":ScopeTarget(Identifier("Terminal_Local"),"terminal_local")}
        self.actionScopeNames = {}#Need to specify and deal with this with a generic
        self.assignments = {}
        self.parent = parent
        #resolvable monster scope
    def addNodes(self,nodeList):
        self.nodes = nodeList
    def __str__(self):
        result = ""
        result += ''.join(("%s -> %s\n"%(item,str(value)) for item, value in self.scopeNames.items()))
        result += ''.join(("%s -> %s\n"%(item,str(value.target)) for item, value in self.actionScopeNames.items()))
        result += '\n'.join(map(lambda x: str(x), self.nodes))
        return result
    def substituteScopes(self):
        moduleScopes = self.scopeNames
        actionScopes = self.actionScopeNames
        for node in self.nodes:
            node.substituteScopes(moduleScopes,actionScopes)
    def resolveScopeToModule(self, modulemap):
        for node in self.nodes:
            node.resolveScopeToModule(modulemap)
    def resolveTerminals(self):
        for node in self.nodes:
            node.resolveTerminals(self.nodeByName,self.assignments)
    def scopeStringToScopeObject(self,root,modules,namedScopes,indexedScopes):
        dependencies = {}
        inverseDependencies = {}
        for scopeName,scope in self.scopeNames.items():
            if scope.isModule():
                path = str(scope.resolve(root,modules,namedScopes,indexedScopes).absolute())
                if path not in modules:
                    module = np.THKModule(path,None,None,self.settings,external=True,
                                          parent = self.parent.parent if self.parent else None)
                    modules[path] = module
                    module.scopeStringToScopeObject(root,modules,namedScopes,indexedScopes)
                else:
                    module = modules[path]
                dependencies[scopeName] = module
                inverseDependencies[str(module.path)] = module
        self.scopeMappings = dependencies
        self.dependencyPath = inverseDependencies
        return dependencies
    def getNodeData(self):
        errorlog = self.errorHandler
        unindexedNodes = []
        indexedNodes = {}
        names = {}
        ids = {}
        unidentified = []
        usedIDs = set()
        for node in self.nodes:
            if node.indexed():
                ix = node.getIndex()
                if ix in indexedNodes:
                    errorlog.repeatedIndex()
                indexedNodes[ix] = node
            else:
                unindexedNodes.append(node)
            for name in node.names():
                if name in names:
                    errorlog.repeatedName()
                names[name] = node
            if node.hasId():
                iD = node.getId()
                if iD in ids:
                    errorlog.repeatedId()
                ids[iD] = node
            else:
                unidentified.append(node)
        return unindexedNodes,indexedNodes,unidentified,names,ids
    def mapLocalNodeNames(self):
        nodeData = self.getNodeData()
        variableNames = self.assignments
        unindexedNodes,indexedNodes,unidentifiedNodes,names,ids = nodeData
        idSet = set(ids.keys())
        idSet.add(0)
        self.nodeByName = names
        self.nodeByIndex = ids
        self.idGen = Autonumber(idSet)
        self.indexGen = Autonumber(indexedNodes.keys())
        for index,node in zip(self.indexGen,unindexedNodes):
            node.setIndex(index)
            indexedNodes[index] = node
        for iD,node in zip(self.idGen,unidentifiedNodes):
            node.setId(iD)
            ids[iD] = node
        for node in self.nodes:
            node.resolveImmediateCalls(indexedNodes,names,variableNames)
    def resolveInlines(self):
        self.inlineNamespace = defaultdict(dict)
        self.inlineAdditions = defaultdict(list)
        for node in self.nodes:
            node.resolveInlines(self,self.dependencyPath)
        self.inlineCleanup()
    def hasInlineCall(self,scope_n_name):
        #print("hasInlineCall",scope_n_name)
        scope,name = scope_n_name
        if scope in self.inlineNamespace:
            return name in self.inlineNamespace[scope]
        return False
    def importInline(self,module,function):
        path = str(module.path)
        nodecopies = module.returnInline(function)
        for node in nodecopies:
            if not any((name in self.inlineNamespace[path] for name in node.names())):
                for name in node.names():
                    self.inlineNamespace[path][name] = node
                self.inlineAdditions[path].append(node)
                node.resolveLocal(self.nodeByName,self.assignments)
    def returnInLine(self,functionName):
        node = self.nodeByName[functionName]
        return node.chainedCopy(set())
    def inlineCleanup(self):
        indexGen = self.indexGen
        idGen = self.idGen
        for path in self.inlineNamespace:
            inline_namespace = self.inlineNamespace[path]
            additions = self.inlineAdditions[path]
            for node in additions:
                node.setIndex(next(indexGen))
                node.setId(next(idGen))
                node.renameToScope(path)
                node.resolveImmediateCalls({},inline_namespace,{})
                for name in node.names():
                    self.nodeByName[name] = node
                self.nodeByIndex[node.getIndex()] = node       
                node.resolveLocal(self.nodeByName,self.assignments)
                self.nodes.append(node)
        for node in self.nodes:
            node.inlinedLocalCallScopeResolution(self.inlineNamespace)
        return
    def resolveCalls(self):
        for node in self.nodes:
            node.resolveCalls()
    def resolveActions(self,entityManager,projectMonster = None):
        if len(self.actionScopeNames) == 0:
            fileMonster = projectMonster
        elif len(self.actionScopeNames) == 1:
            monsterTarget = next(iter(self.actionScopeNames.values()))
            fileMonster = monsterTarget.resolve(entityManager)
        elif len(self.actinoScopeNames) >= 2:
            monsterTarget = [self.actionScopeNames[scope] for scope in self.actionScopeNames if scope != "generic"][0]
            fileMonster = monsterTarget.resolve(entityManager)
        self.actionScopeNames["monster"] = fileMonster
        self.monsterID = fileMonster.monsterID if fileMonster else 0
        for node in self.nodes:
            try:
                node.resolveActions(self.actionScopeNames)
            except:
                if projectMonster is None:
                    node.errorHandler.missingAnyActionScope()
                else:
                    raise
    def collectRegisters(self):
        registerListing = set()
        for node in self.nodes:
            registerListing = registerListing.union(set(node.collectRegisters()))
        return registerListing
    def resolveFunctions(self,functionResolver):
        for node in self.nodes:
            node.resolveFunctions(functionResolver)
    def resolveRegisters(self,namespace):
        for node in self.nodes:
            node.resolveRegisters(namespace)
    def compileProperties(self):
        indexGen = Autonumber()
        visited = 0
        realCount = len(self.nodeByIndex)
        serialNodes = []
        while visited < realCount:
            index = next(indexGen)
            if index in self.nodeByIndex:
                node = self.nodeByIndex[index]
                visited += 1
            else:
                header = NodeHeader(["Dummy::Node_%03d"%index], (0,index), -1)
                s = Segment()
                s.addEndNode()
                bodylist = [s]
                node = Node(header,bodylist)
                self.inheritChildren(node)
                node.inherit()
                self.nodeByIndex[index] = node   
                self.nodes.append(node)
                for name in node.names():
                    self.nodeByName[name] = node
            serialNodes.append(node.compileProperties())
        headerSize = 0x20
        baseOffset = 0x10+len(serialNodes)+headerSize
        offset = baseOffset
        for node in serialNodes:
            node["offset"] = offset
            offset += node["count"]*0x80
        self.dataSerialNodes = serialNodes
        self.dataHeader = {"signature":"THK\x00".encode("utf-8"), "formatVersion":40,
                             "headerSize":headerSize,"isPalico":"otomo" in self.actionScopeNames,
                             "monsterID":self.monsterID,"unknownHash":314159,
                             "structCount":len(serialNodes)}
    def serialize(self):
        return thk.Thk.build({"header":self.dataHeader,"nodelist":self.dataSerialNodes})+compilerSignature
    
class ScopeTarget(ErrorManaged):
    subfields = []
    def __init__(self,target,type):
        tag = "Module Scope Namespace [%s -> %s]"%(str(target),type)
        self.target = str(target)
        self.type = type
        #path,id,ix,local,terminal_local
    def isModule(self):
        return self.type not in ["local","terminal_local"]
    def resolve(self,root,modules,namedScopes,indexedScopes):
        settings = self.settings
        if self.type == "path":
            path = (root/self.target).absolute()
        elif self.type == "id":
            if self.target not in namedScopes:
                settings.compiler.missingScope(self.target)
            path = namedScopes[self.target].path
        elif self.type == "ix":
            if self.target > len(indexedScopes):
                settings.compiler.indexOverflow(self.target)
                raise SemanticError("%d exceedsd the number of thk indices"%self.target)
            if indexedScopes[self.target][0] == "":#TODO - Encapsulate the indexed scopes into objects instead of tuples
                settings.compiler.emptyScope(self.target)
            path = indexedScopes[self.target]
        else:
            raise SemanticError("Local and Terminal Local cannot resolve to paths.")
        self.path = path
        return path
    def resolveScopeToModule(self,modulemap):
        if self.type not in ["local","terminal_local"]:
            self.module = modulemap[str(self.path.absolute())]
            #print("rstm-st",self.module)
            return self.module
    def __str__(self):
        return str(self.target)
    def copy(self):
        st = ScopeTarget(copy(self.target), copy(self.type))
        if hasattr(self,"path"):st.path = self.path
        return st
class ActionTarget(ErrorManaged):
    subfields = []
    def __init__(self,target,typing):
        self.tag = "Action Scope Namespace [%s]"%str(target)
        self.target = target
        self.typing = typing
    def copy(self):
        return ActionTarget(copy(self.target,self.typing))
    def resolve(self,entityManager):
        if self.typing == "id":
            try:
                self.nameToId,self.idToName = entityManager.actionsByName(self.target)
                self.monsterID = entityManager[self.target].gameID
            except:
                self.errorHandler.invalidMonsterName(self.target)
                self.nameToId,self.idToName = {},{}
                self.monsterID = -1
        elif self.typing == "path":
            self.monsterID = -1
            path = Path(self.target)
            if not path.is_absolute():
                path = self.settings.compiler.root/path
            try:
                self.nameToId,self.idToName = parseActionFile(path)
            except:
                self.errorHandler.invalidActionFile(path)         
                self.nameToId,self.idToName = {},{}
    def resolveAction(self,actionName):
        if actionName in self.resolutions:
            return self.nameToId[actionName]
        else:
            self.errorHandler.missingActionName(actionName)
            return -1
    def checkIndex(self,actionIndex):
        return actionIndex in self.idToName
class Node(ErrorManaged):
    subfields = ["bodylist","header"]
    def __init__(self,header,bodylist):
        self.header = header
        self.bodylist = bodylist
        #print(self.header.lineno)
        self.tag = "Node [%s] at line %d"%(self.names()[0],self.header.lineno)
    def indexed(self):
        return self.header.index is not None
    def hasId(self):
        return self.header.id is not None
    def getId(self):
        return self.header.id
    def setId(self,val):
        self.header.id = val
    def getIndex(self):
        return self.header.index
    def setIndex(self,val):
        self.header.index = val
    def names(self):
        return self.header.names
    def renameToScope(self,scope):
        self.header.names = [scope+"::"+n for n in self.header.names]
    def __str__(self):
        result = ""
        result += str(self.header) + "\n"
        result += ''.join((str(b) + '\n' for b in self.bodylist))
        return result
    def resolveScopeToModule(self,modulemap):
        for segment in self.bodylist:
            segment.resolveScopeToModule(modulemap)
    def substituteScopes(self,moduleScopes,actionScopes):
        for segment in self.bodylist:
            segment.substituteScopes(moduleScopes,actionScopes)
    def resolveImmediateCalls(self,nodeIndex,nodeNames,variableNames):
        for segment in self.bodylist:
            segment.resolveImmediateCalls(nodeIndex,nodeNames,variableNames)    
    def resolveInlines(self,controller,scopes):
        for segment in self.bodylist:
            inlineCall = segment.inlineCall()
            if inlineCall:
                scope,target = inlineCall
                if not controller.hasInlineCall(inlineCall):
                    controller.importInline(scopes[scope],target)
    def inlinedLocalCallScopeResolution(self,namespaces):
        for segment in self.bodylist:
            segment.inlinedLocalCallScopeResolution(namespaces)
    def copy(self):
        header = copy(self.header)
        bodylist = [copy(segment) for segment in self.bodylist]
        return Node(header,bodylist)
    def chainedCopy(self,chainMembers):
        copies = []
        for segment in self.bodylist:
            if segment.internalCall():
                node = segment.callTarget()
                if node not in chainMembers:
                    chainMembers.add(node)
                    copies += node.chainedCopy(chainMembers)
        copies.append(copy(self))
        return copies
    def resolveLocal(self,namespace,assignments):
        for segment in self.bodylist:
            segment.resolveLocal(namespace,assignments)
    def resolveTerminals(self,nodeNames,assignments):
        for segment in self.bodylist:
            segment.resolveTerminals(nodeNames,assignments)
    def resolveCalls(self):
        for segment in self.bodylist:
            segment.resolveCalls()
    def resolveActions(self,actionScopes):
        for segment in self.bodylist:
            segment.resolveActions(actionScopes)
    def collectRegisters(self):
        registers = set()
        for segment in self.bodylist:
            registers = registers.union(segment.collectRegisters())
        return registers
    def resolveRegisters(self,namespace):
        for segment in self.bodylist:
            segment.resolveRegisters(namespace)
    def resolveFunctions(self,functionResolver):
        for segment in self.bodylist:
            segment.resolveFunctions(functionResolver)
    def compileProperties(self):
        segmentList = []
        for segment in self.bodylist:
            dataSegment = segment.compileProperties
            if dataSegment: segmentList.append(dataSegment)
        self.binaryStructure = {"offset":0,"count":len(segmentList),"id":self.getId(),
                                "segments":segmentList}
        return self.binaryStructure
class NodeHeader(ErrorManaged):
    subfields = []
    def __init__(self,aliaslist,index,lineno):
        self.names = [str(alias) for alias in aliaslist]
        self.id,self.index  = index
        self.lineno = lineno
        self.tag = "Node Header [%s]"%self.names[0]
    def __str__(self):
        return "def " + ' & '.join(map(str,self.names)) + ":"
    def copy(self):
        return NodeHeader(self.names,(self.id,self.index),self.lineno)
class TypeNub(ErrorManaged):
    def __init__(self,propName,raw_id):
        self.propName = propName
        self.tag = propName
        self.raw_id = raw_id
    def resolveProperties(self,storage):
        storage(self.propName,self.raw_id)
    def copy(self):
        return type(self)(self.propName,self.raw_id)
class ChanceNub(TypeNub):
    def resolveProperties(self,storage):
        super().resolveProperties(storage)
class DeferredNub(TypeNub):
    def resolveProperties(self,storage):
        storage(self.propName,self.raw_id())
class Segment(ErrorManaged):
    memberList = ["function","call","directive","action","branchingControl","randomType",
                  "terminator","metaparams","chance"]
    subfields = ["_"+m for m in memberList]
    tag = "Node Segment"
    def __init__(self):
        self._function = None
        self._call = None
        self._directive = None
        self._action = None
        self._branchingControl = None
        self._randomType = None
        self._terminator = None
        self._metaparams = {}
        self._chance = None
    def copy(self):
        s = Segment()
        for f in self.memberList:
            field = "_"+f
            setattr(s,field,copy(getattr(self,field)))
        return s
    def existingCheck(self,check):
        if getattr(self,"_"+check) is not None:
            raise SemanticError("Segment already has been assigned a %s"%check)
    def addFunction(self,function):
        self.existingCheck("function")
        self._function = function
    def addAction(self,action):
        self.existingCheck("action")
        self._action = action
    def addCall(self,call):
        self.existingCheck("call")
        self._call = call
    def addDirective(self,directive):
        self.existingCheck("directive")
        self._directive = directive
    def startConditional(self):
        self.existingCheck("branchingControl")
        self._branchingControl = TypeNub("branchingControl",0x2)
    def addConditionalBranch(self):
        self.existingCheck("branchingControl")
        self._branchingControl = TypeNub("branchingControl",0x4)
    def endConditional(self):
        self.existingCheck("branchingControl")
        self._branchingControl = TypeNub("branchingControl",0x8)
    def addEndNode(self):
        self.existingCheck("randomType")
        self._randomType = TypeNub("endRandom",0x1)
        self._terminator = DeferredNub("nodeEndingData",self.getNodeId)
    def addChance(self,chance):
        self.existingCheck("chance")
        self._chance = chance
    def endChance(self):
        self.existingCheck("branchingControl")
        self._branchingControl = ChanceNub("branchingControl",0x1)
    def addConclude(self):
        self.existingCheck("branchingControl")
        self._branchingControl = TypeNub("branchingControl",0x10)
    def addMeta(self,params):
        self._metaparams = params
    def getNodeId(self):
        return self.parent.getId()
    def substituteScopes(self,moduleScopes,actionScopes):
        for member in ["call","action"]:
            value = getattr(self,"_"+member)
            if value is not None:
                value.substituteScope(moduleScopes,actionScopes)
    def resolveScopeToModule(self,modulelist):
        if self._call is not None:
            self._call.resolveScopeToModule(modulelist)
    def resolveImmediateCalls(self,localIndices,localNames,variableNames):
        self._resolutionOperator(localIndices,localNames,variableNames,
                                     "immediateResolve","resolveImmediateId")
    def _resolutionOperator(self,localIndices,localNames,variableNames,
                                callResolution,fieldResolution):
        if callResolution:
            if self._call is not None:
                getattr(self._call,callResolution)(localIndices,localNames)
        if fieldResolution:
            for field in ["function","action"]:
                fieldVal = getattr(self,"_"+field)
                if fieldVal is not None:
                    getattr(fieldVal,fieldResolution)(variableNames)
            if self._chance:
                getattr(self._chance,fieldResolution)(variableNames)
    def inlinedLocalCallScopeResolution(self,namespace):        
        self._resolutionOperator({},namespace,{},"inlinedLocalCallScopeResolution","")
    def __str__(self):
        return ','.join([attr if not attr == "branchingControl" else self._branchingControl
            for attr in ["function","call","action","directive","branchingControl",
                         "randomType","terminator","metaparams"]
            if getattr(self,"_"+attr) is not None])
    def internalCall(self):
        if self._call:
            return self._call.internalCall()
        return False
    def inlineCall(self):
        if self._call:
            return self._call.inlineCall()
        return False
    def callTarget(self):
        if self._call:
            return self._call.node_target
        raise SemanticError("Non-Call Segment does not have a Call Target")
    def resolveLocal(self,nodeNames,variableNames):
        self._resolutionOperator({},nodeNames,variableNames,
                                     "resolveLocal","resolveLocalId")
    def resolveTerminals(self,nodeNames,variableNames):
        self._resolutionOperator({},nodeNames,variableNames,
                                     "resolveTerminals","resolveTerminalId")
    def resolveCalls(self):
        if self._call:
            return self._call.resolveCalls()
    def resolveActions(self,actionScopes):
        if self._action:
            self._action.resolveAction(actionScopes)
    def collectRegisters(self):
        if self._function and self._function.typing == "register": #else function
            return self._function.collectRegisters()
        else:
            return []
    def resolveRegisters(self,namespace):
        if self._function and self._function.typing == "register": #else function
            return self._function.resolveName(namespace)
    def resolveFunctions(self,functionResolver):
        if self._function:
            self._function.resolveFunctions(functionResolver)
    def compileProperties(self):
        dataSegment = {}
        def testAdd(propertyName,propertyValue):
            if propertyName in dataSegment:
                self.errorHandler.repeatedProperty(propertyName)
            dataSegment[propertyName] = propertyValue
        for member in self.memberList:
            var = getattr(self,"_"+member)
            if member == "metaparams":
                pass
            else:
                if var: var.compileProperties(testAdd)
        for key,val in self._metaparams.items():
            if hasattr(val,"raw_id"): testAdd(key,val)
            else: val.erroHandler.unresolvedIdentifier()
        if "functionID" not in dataSegment: 
            default = 0 if "endChance" in dataSegment else 2
            dataSegment["functionID"] = default
        for field in thk.Segment.subcons:
            name = field.name
            if field.name not in dataSegment:
                dataSegment[field.name] = 0
        return dataSegment
class Chance(ErrorManaged):
    subfields = ["chance"]
    def __init__(self,percentage):
        tag = "Stochastic Choice [%s]"%percentage
        self.chance = percentage
    def copy(self):
        return Chance(self.chance)
    def resolveIds(self,variableNames,operator):
        getattr(self.chance,operator)(variableNames)
    def resolveImmediateId(self,variableNames):
        self.resolveIds(variableNames,"resolveImmediateId")
    def resolveLocalId(self,variableNames):
        self.resolveIds(variableNames,"resolveLocalId")
    def resolveTerminalId(self,variableNames):
        self.resolveIds(variableNames,"resolveTerminalId")
    def resolveProperties(self,storage):
        storage("parameter1",self.chance)
class ChanceHead(Chance):
    def resolveProperties(self,storage):
        storage("endRandom",0x40)
        super().resolveProperties(storage)        
class ChanceElse(Chance):
    def last(self):
        return ChanceLast(self.chance)
    def resolveProperties(self,storage):
        storage("endRandom",0xC0)
        super().resolveProperties(storage)    
class ChanceLast(Chance):
    def resolveProperties(self,storage):
        storage("endRandom",0x80)
        super().resolveProperties(storage)    
class FunctionShell(ErrorManaged):
    typing = "function"
    subfields = ["sections","params"]
    def __init__(self,id=None,params=None):
        if id is None:
            self.tag = "Function Call Name"
            self.sections = []
            self.params = []
        else:
            self.tag = "Function Call Name [%s]"%id
            self.sections = [id]
            self.params = [params]
    def extend(self,other):
        self.sections += other.sections
        self.params += other.params
    def parameterResolution(self,varNames,operator):
        for paramGroup in self.params:
            for param in paramGroup:
                try:
                    getattr(param,operator)(varNames)
                except SemanticError:
                    pass
    def resolveImmediateId(self,varNames):
        self.parameterResolution(varNames,"resolveImmediateId")
    def resolveLocalId(self,varNames):
        self.parameterResolution(varNames,"resolveLocalId")
    def resolveTerminalId(self,varNames):
        self.parameterResolution(varNames,"resolveTerminalId")    
    def copy(self):
        shell = FunctionShell()
        shell.sections = [copy(id) for id in self.sections]
        shell.params = [[copy(p) for p in params] for params in self.params]
        return shell
    def resolveProperties(self,storage):
        storage("functionType",self.raw_id)
        for field,parameterValue in self.functionParamPairs:
            storage(field,parameterValue)
    def resolveFunctions(self,functionResolver):
        parameters = {}
        def testAdd(propertyName,propertyValue):
            if propertyName in parameters:
                self.errorHandler.repeatedProperty(propertyName)
            parameters[propertyName] = propertyValue
        functionResolver(self,testAdd)
        self.functionParamPairse = list(parameters.items())
    def signature(self):
        sig = []
        for literal,param in zip (self.sections,self.params):
            sig.append(-1)
            sig.append(len(param))
        return tuple(sig)
    def literalSignature(self):
        return tuple(map(str,self.sections))
class FunctionLiteral(ErrorManaged):
    typing = "function"
    subfields = ["function","arguments"]
    def __init__(self,function,arguments):
        self.tag = "Function Call Literal [%X]"%function
        self.function = function
        self.raw_id = function
        self.arguments = arguments
    def copy(self):
        return FunctionLiteral(copy(self.function),[copy(arg) for arg in self.arguments])
    def parameterResolution(self,varNames,operator):
        for paramGroup in self.arguments:
            for param in paramGroup:
                try:
                    getattr(param,operator)(varNames)
                except SemanticError:
                    pass
    def resolveImmediateId(self,varNames):
        self.parameterResolution(varNames,"resolveImmediateId")
    def resolveLocalId(self,varNames):
        self.parameterResolution(varNames,"resolveLocalId")
    def resolveTerminalId(self,varNames):
        self.parameterResolution(varNames,"resolveTerminalId")
    def resolveProperties(self,storage):
        storage("functionType",self.raw_id)
        for field,parameterObj in zip(["parameter1","parameter2"],self.arguments):
            if not hasattr(parameterObj,"raw_id"):
                self.errorHandler.unresolvedParameter()
            else:
                storage(field,parameterObj.raw_id)
    def resolveFunctions(self,_):
        pass
class Register():
    def resolveImmediateId(self,varNames):
        pass
    def resolveLocalId(self,varNames):
        pass
    def resolveTerminalId(self,varNames):
        pass
    def resolveName(self,namespace):
        if hasattr(self,"raw_id"):
            return
        if self.identifier not in namespace:
            self.errorHandler.missingRegisterName(self.identifier)
        else:
            self.raw_id = namespace[self.identifier]
    def collectRegisters(self):
        if hasattr(self,"raw_id"):
            return [self.raw_id]
        else:
            return [str(self.identifier)]
class RegisterID(Register,ErrorManaged):
    tag = "Register ID"
    subfields = ["identifier"]
    def __init__(self,id):
        self.tag = "Register ID [%s]"%(id)
        self.identifier = id
    def copy(self):
        return RegisterID(copy(self.identifier))
class RegisterLiteral(Register,ErrorManaged):
    tag = "Register Literal"
    subfields = ["identifier"]
    def __init__(self,id):
        self.tag = "Register ID [%s]"%(id)
        self.identifier = id
        self.raw_id = id
    def copy(self):
        return RegisterID(copy(self.identifier))
class RegisterOp():
    typing = "register"
    def resolveImmediateId(self,varNames):
        pass
    def resolveLocalId(self,varNames):
        pass
    def resolveTerminalId(self,varNames):
        pass
    def resolveName(self,namespace):
        self.base.resolveName(namespace)    
    def collectRegisters(self):
        return self.base.collectRegisters()
    
regSymbols = ["==","<=" ,"<" ,">=" ,">" ,"!="]
regComps = {regSymbols[i]:i for i in range(len(regSymbols))}
class RegisterComparison(RegisterOp,ErrorManaged):
    subfields = ["base","target","comparison"]
    def __init__(self,ref,val,comp):
        self.tag = "Register Comparison [%s %s %s]"%(ref,comp,val)
        self.base = ref
        self.target = val
        self.comparison = comp
    def copy(self):
        return RegisterComparison(copy(self.base),
                                  copy(self.target),
                                  copy(self.comparison))
    def parameterResolution(self,varNames,operator):
        getattr(self.target,operator)(varNames)
    def resolveImmediateId(self,varNames):
        self.parameterResolution(varNames,"resolveImmediateId")
    def resolveLocalId(self,varNames):
        self.parameterResolution(varNames,"resolveLocalId")
    def resolveTerminalId(self,varNames):
        self.parameterResolution(varNames,"resolveTerminalId")
    def resolveProperties(self,storage):
        if not hasattr(self.base,"raw_id"):
            self.errorHandler.unresolvedIdentifier(str(self.base))
        elif not hasattr(self.target,"raw_id"):
            self.errorHandler.unresolvedIdentifier(str(self.target))
        else:
            storage("functionType",0x94+self.base.raw_id)
            storage("parameter1",regComps[self.comparison])
            storage("parameter2",self.target.raw_id)
unaryOps = {"++":0,"|-":1}
class RegisterUnaryOp(RegisterOp,ErrorManaged):
    tag = "Register Unary Operator"
    subfields = ["base","operator"]
    def __init__(self,ref,op):
        self.base = ref
        self.operator = op
    def copy(self):
        return RegisterUnaryOp(copy(self.base),copy(self.operator))
    def resolveProperties(self,storage):
        if not hasattr(self.base,"raw_id"):
            self.errorHandler.unresolvedIdentifier(str(self.base))
        else:
            storage("functionType",0x94+self.base.raw_id)
            storage("parameter1",unaryOps[self.operator])
class Action(ErrorManaged):
    tag = "Action"
    subfields = ["parameters"]
    def __init__(self):
        self.parameters = []
    def addParameters(self,parameters):
        self.parameters += parameters
    def copy(self,*args,**kwargs):
        a = type(self)(*args,**kwargs)
        a.parameters = [copy(p) for p in self.parameters]
        return a
    def parameterResolution(self,varNames,operator):
        for param in self.parameters:
            getattr(param,operator)(varNames)
    def resolveImmediateId(self,varNames):
        self.parameterResolution(varNames,"resolveImmediateId")
    def resolveLocalId(self,varNames):
        self.parameterResolution(varNames,"resolveLocalId")
    def resolveTerminalId(self,varNames):
        self.parameterResolution(varNames,"resolveTerminalId")      
    def legalIndex(self,actionMap,id):
        if not any((mapping.checkIndex(id) for mapping in actionMap)):
            self.errorHandler.illegalActionIndex(id)
    def resolveProperties(self,storage):
        if not hasattr(self,"raw_id"):
            self.errorHandler.unresolvedIdentifier()
        else:
            storage("actionID",self.raw_id)
            for ix,param in enumerate(self.parameters):
                if ix >= 5:
                    param.errorHandler.actionParameterCountExceeded(ix)
                    continue
                if hasattr(param,"raw_id"):
                    storage("actionUnkn%d"%ix,param.rawID)
                else:
                    param.errorHandler.unresolvedIdentifier()
class ActionLiteral(Action):
    def __init__(self,id):
        tag = "Action Literal [%d]"%id
        self.raw_id = id
        super().__init__()
    def substituteScope(self,*arg,**kwargs):
        pass
    def copy(self):
        return super().copy(copy(self.raw_id))
    def resolveAction(self,actionMap):
        self.legalIndex(actionMap,self.raw_id)
class ActionID(Action): 
    subfields = ["parameters","id"]
    def __init__(self,name):
        self.tag = "Action ID [%s]"%name
        self.id = name
        super().__init__()
    def substituteScope(self,*arg,**kwargs):
        pass
    def copy(self):
        return super().copy(copy(self.id))
    def resolveAction(self,actionMap):
        if not hasattr(self.id, "raw_id"):
            self.errorHandler.unresolvedIdentifier(self.id)
            return
        self.raw_id = self.id.raw_id
        self.legalIndex(actionMap,self.raw_id)
class ScopedAction(Action): 
    subfields = ["parameters","id","scope"]
    def __init__(self,scope,name):
        self.tag = "Action Scoped ID [%s.%s]"%(str(scope),str(name))
        self.scope = str(scope)
        self.id = str(name)
        super().__init__()
    def substituteScope(self,moduleScope,actionScope):
        pass
    def copy(self):
        return super().copy(copy(self.scope),copy(self.id))
    def resolveAction(self,actionMap):
        if self.scope not in actionMap:
            self.errorHandler.missingActionScope(self.scope)
            return
        scope = actionMap[self.scope]
        self.raw_id = scope.resolveAction(self.id)
class Call(ErrorManaged):
    subfields = ["target"]
    local_scope = "indices"
    def __init__(self,ix):
        self.tag = "Call [%s]"%str(ix)
        self.target = ix
    def resolveCalls(self):
        if hasattr(self,"raw_target"):
            return
        self.raw_target = self.node_target.getId()
        self.external = -1
    def immediateResolve(self,localIndices,localNames):
        self._immediateResolve(indices = localIndices, names = localNames)
    def _immediateResolve(self,**kwargs):
        if self.target not in kwargs[self.local_scope]:
            self.errorHandler.missingNodeName(self.target)
            #raise SemanticError("Call refers to non-existant member of node %s %s"%(self.local_scope,self.target))
        self.node_target = kwargs[self.local_scope][self.target]
    def resolveLocal(self,localIndices,localNames):
        pass
    def resolveTerminals(self,localIndices,localNames):
        pass
    def internalCall(self):
        return True
    def inlineCall(self):
        return False
    def inlinedLocalCallScopeResolution(self,_,__):
        pass
    def resolveScopeToModule(self,modulelist):
        pass
    def copy(self):
        c = Call(copy(self.raw_target),copy(self.target))
        if hasattr(self,"node_target"):
            c.node_target = self.node_target
        return c
    def resolveProperties(self,storage):
        if not hasattr(self,"raw_target"):
            self.errorHandler.unresolvedIdentifier()
        else:
            if self.external == -1:
                storage("extRefThkID",self.external)
                storage("extRefNodeID",self.external)
                storage("localRefNodeID",self.raw_target)
            else:
                storage("extRefThkID",self.external)
                storage("extRefNodeID",self.raw_target)
                storage("localRefNodeID",-1)                
class CallID(Call):
    local_scope = "names"
    def __init__(self,namedId):
        self.tag = "Call ID [%s]"%namedId
        self.target = str(namedId)
    def substituteScope(self,*arg,**kwargs):
        pass
    def inlineCall(self):
        return False
    def internalCall(self):
        return True
    def resolveScopeToModule(self,modulelist):
        pass
    def copy(self):
        c = CallID(copy(self.target))
        c.node_target = self.node_target
        return c
class ScopedCallID(Call):
    subfields = ["target","scope"]
    def __init__(self,scope,target):
        self.tag = "Call Scoped ID [%s.%s]"%(scope,target)
        self.scope = str(scope)
        self.target = str(target)
        self.node_target = None
    def substituteScope(self,moduleScope,actionScope):
        if self.scope in moduleScope:
            self.scope = moduleScope[self.scope]
        else:
            self.errorHandler.missingImport(self.scope)
            #raise SemanticError("%s is not within the file's import list"%self.scope)
    def immediateResolve(self,*args,**kwargs):
        pass
    def scopeResolve(self,localIndices,localNames,typing):
        if self.scope.type == typing:
            if self.target in localNames: self.node_target = localNames[self.target]
            else: self.errorHandler.missingNodeName(self.target,str(self.scope))
    def resolveLocal(self,localIndices,localNames):
        self.scopeResolve(localIndices,localNames,"local")
    def resolveTerminals(self,localIndices,localNames):
        self.scopeResolve(localIndices,localNames,"terminal_local")
    def resolveScopeToModule(self,modulelist):
        module = self.scope.resolveScopeToModule(modulelist)
        self.module = module
    def inlinedCallScopeResolution(self,indices,namespaces,typing):
        if self.scope.type ==typing:
            if self.module.inlineCall:
                path = str(self.module.path)
                if path in namespaces:
                    module = namespaces[str(self.module.path)]
                    if self.target in module:
                        self.node_target = module[self.target]
                    else:
                        self.errorHandler.missingNodeName(self.target,module.scopeName if module.scopeName else path)
                else:
                    self.errorHandler.missingModule(path)
    def internalCall(self):
        return False
    def inlineCall(self):
        if self.module and self.module.inlineCall:
            return str(self.module.path),self.target
        else:
            return False
    def copy(self):
        sc = type(self)("",copy(self.target))
        sc.scope = copy(self.scope)
        if hasattr(self,"module"):
            sc.module = self.module
        return sc
    def resolveCalls(self):
        if hasattr(self,"raw_target"):
            return
        try:
            self.raw_target = self.module.getNodeIndexByName(self.target)
        except:
            self.errorHandler.missingNodeName(self.target)
        self.external = self.module.id
class ScopedCall(ScopedCallID):
    tag = "Call Scoped Literal"
    def resolveCalls(self):
        if hasattr(self,"raw_target"):
            return
        try:
            self.raw_target = self.module.getNodeIndexByIndex(self.target)
        except:
            self.errorHandler.getNodeIndexByIndex(self.target)
        self.external = self.module.id
        
fDirectiveMap = {"return":0x8,"repeat":0x4,"reset":0x80}
bDirectiveMap = {v:k for k,v in fDirectiveMap.items()}
class Directive(ErrorManaged):
    tag = "Directive"
    subfields = []
    def __init__(self,command):
        self.raw_target = fDirectiveMap[command]
    def copy(self):
        return Directive(bDirectiveMap[self.raw_target])
    def resolveProperties(self,storage):
        storage("flowControl",self.raw_target)
                 
class Identifier(ErrorManaged):
    subfields = ["id"]
    def __init__(self,identifier):
        self.tag = "Identifier [%s]"%str(identifier)
        self.id = identifier
    def __str__(self):
        return str(self.id)
    def resolveLocalId(self,variableNames):
        pass
    def resolveTerminalId(self,variableNames):
        pass
    def resolveImmediateId(self,variableNames):
        if self.id not in variableNames:
            self.errorHandler.missingVariableName(self.id)
        self.raw_id = variableNames[self.id]
    def copy(self):
        return Identifier(copy(self.id))
    def verifyEnum(self,_):
        return False
class IdentifierRaw(ErrorManaged):
    subfields = ["raw_id"]
    def __init__(self,identifier):
        self.tag = "Identifier Literal [%s]"%str(identifier)
        self.raw_id = identifier
    def resolveImmediateId(self,_):
        return
    def resolveTerminalId(self,variableNames):
        pass
    def resolveLocalId(self,variableNames):
        pass
    def __str__(self):
        return str(self.raw_id)
    def copy(self):
        return IdentifierRaw(copy(self.raw_id))
    def verifyEnum(self,enumManager):
        return self.raw_id in enumManager
    def accessEnum(self,enumManager):
        return self.raw_id
class FunctionScopedId(ErrorManaged):
    tag = "Function Scoped ID"
    subfields = ["target","scope"]
    def __init__(self,scope,target):
        self.scope = scope
        self.target = target
    def __str__(self):
        return str(self.scope) + "." + str(self.target)
    def scopeResolve(self,variableNames,typing):
        if str(self.scope) == typing:
            if self.target in variableNames:
                self.raw_id = variableNames[self.target]
            else:
                self.errorHandler.missingNodeName(self.target,str(self.scope))
    def resolveLocalId(self,variableNames):
        self.scopeResolve(variableNames,"Local")
    def resolveTerminalId(self,variableNames):
        self.scopeResolve(variableNames,"Terminal_Local")
    def resolveImmediateId(self,variableNames):
        return
    def copy(self):
        return FunctionScopedId(copy(self.scope),copy(self.target))
    def verifyEnum(self,enumManager):
        return str(self.scope) == enumManager.scope and str(self.target) in enumManager
    def accessEnum(self,enumManager):
        return enumManager[str(self.target)]
class TextID(str,ErrorManaged):
    tag = "Text ID"
    subfields = []
    def copy(self):
        return TextID(self)