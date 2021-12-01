# -*- coding: utf-8 -*-
"""
Created on Thu Nov 25 04:52:08 2021

@author: Asterisk
"""
from signatures import compilerSignature
from errorHandler import ErrorManaged,copy
from actionEnum import parseActionFile
from compilerUtils import Autonumber
import thk
import nackParse as np
from .nackIdentifier import Identifier
from .nackNode import NodeHeader,Node
from .nackSegment import Segment

from pathlib import Path
from collections import defaultdict

class SymbolsTable():
    def __init__(self):
        self.namespaces = {}
        self.nodes = {}
        self.nodeIndices = {}
        self.nodeIds = {}
        self.vars = {}
    def addNamespace(self,scope,target):
        self.namespaces[scope] = target
    def addNode(self,nodeNames,nodeIndex,nodeId,nodeObject):
        for nodeName in nodeNames:
            self.nodes[nodeName] = nodeObject
        self.nodeIndices[nodeIndex] = nodeObject
        self.nodeIndices[nodeId] = nodeObject
    def addVar(self,key,val):
        self.vars[key] = val
    
class ScopeTarget(ErrorManaged):
    subfields = []
    def __init__(self,target,type):
        tag = "Module Scope Namespace [%s -> %s]"%(str(target),type)
        self.target = str(target)
        self.type = type
        #path,id,ix,local,terminal_local
    def isModule(self):
        return self.type not in ["caller","terminal_caller"]
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
                self.errorHandler.thkIndexLimitExceeded()
            if indexedScopes[self.target][0] == "":#TODO - Encapsulate the indexed scopes into objects instead of tuples
                settings.compiler.emptyScope(self.target)
            path = indexedScopes[self.target]
        else:
            return
            #raise SemanticError("Caller and Terminal Caller cannot resolve to paths.")
        self.path = path
        return path
    def resolveScopeToModule(self,modulemap):
        if self.type not in ["caller","terminal_caller"]:
            self.module = modulemap[str(self.path.absolute())]
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
    
class NackFile(ErrorManaged):
    tag = "Nack File"
    subfields = ["nodes","scopeNames","actionScopeNames"]
    def __init__(self,parent = None):
        self.scopeNames = {"Caller":ScopeTarget(Identifier("Caller"),"caller"),
                           "Terminal_Caller":ScopeTarget(Identifier("Terminal_Caller"),"terminal_caller")}
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
    def createSymbolsTable(self,root,scopeMappings, pathToModule, indexedScopes):
        self.symbolsTable = SymbolsTable()
        for scopeName,scopeTarget in self.scopeNames.items():
            scopeTarget.resolve(root,pathToModule,scopeMappings,indexedScopes)
            self.symbolsTable.addNamespace(scopeName,scopeTarget)

        nodeData = self.getNodeData()
        unindexedNodes,nodeByIndex,unidentifiedNodes,nodeByName,nodeById = nodeData
        idSet = set(nodeById.keys())
        idSet.add(0)
        self.idGen = Autonumber(set(idSet))
        self.indexGen = Autonumber(set(nodeByIndex.keys()))
        for node in unindexedNodes:
            index = next(self.indexGen)
            node.setIndex(index)
            nodeByIndex[index] = node
        for node in unidentifiedNodes:
            iD = next(self.idGen)
            node.setId(iD)
            nodeById[iD] = node
        for node in self.nodes:
            self.symbolsTable.addNode(node.names(),node.getIndex(),node.getId(),node)
        for key,val in self.assignments.items():
            self.symbolsTable.addVariable(key,val)
    def resolveLocal(self):
        for node in self.nodes:
            node.resolveLocal(self.symbolsTable)
    def externalDependencies(self):
        return [scopeTarget.target 
                 for scopeTarget in self.scopeNames.values() 
                 if scopeTarget.type == "path"]
    def resolveLocal(self):
        for node in self.nodes:
            node.resolveLocal(self.symbolsTable)
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
    def resolveInlines(self):
        self.inlineNamespace = defaultdict(dict)
        self.inlineAdditions = defaultdict(list)
        for node in self.nodes:
            node.resolveInlines(self,self.dependencyPath)
        self.inlineCleanup()
    def hasInlineCall(self,scope_n_name):
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
                node.resolveCaller(self.nodeByName,self.assignments)
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
                ix = next(indexGen)
                id = next(idGen)
                node.setIndex(ix)
                node.setId(id)
                node.renameToScope(path)
                node.resolveImmediateCalls({},inline_namespace,{})
                for name in node.names():
                    self.nodeByName[name] = node
                self.nodeByIndex[node.getIndex()] = node    
                self.nodeById[node.getId()] = node    
                node.resolveCaller(self.nodeByName,self.assignments)
                self.nodes.append(node)
        for index in sorted(self.nodeByIndex):
            print("="*15)
            print(index,self.nodeByIndex[index].getIndex())
            print(self.nodeByIndex[index])
            print("="*15)
        for node in self.nodes:
            node.inlinedCallerCallScopeResolution(self.inlineNamespace)
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
        self.dataHeader = {"signature":list("THK\x00".encode("utf-8")), "formatVersion":40,
                             "headerSize":headerSize,"isPalico":"otomo" in self.actionScopeNames,
                             "monsterID":self.monsterID,"unknownHash":314159,
                             "structCount":len(serialNodes)}
    def serialize(self):
        return thk.Thk.build({"header":self.dataHeader,"nodeList":self.dataSerialNodes})+compilerSignature