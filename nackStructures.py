# -*- coding: utf-8 -*-
"""
Created on Fri Oct 29 12:23:10 2021

@author: Asterisk
"""
from compilerErrors import SemanticError
import nackParse as np


def Autonumber(reserved=set()):
    i = 0
    while True:
        while i in reserved: i+=1
        yield i
        i+=1

class NackFile():
    def __init__(self):
        self.scopeNames = {"Local":ScopeTarget(Identifier("Local"),"local"),
                           "Terminal_Local":ScopeTarget(Identifier("Terminal_Local"),"terminal_local")}
        self.actionScopeNames = {"monster":None}#Need to specify and deal with this with a generic
        self.assignments = {}
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
    def resolveScopeNames(self,root,modules,namedScopes,indexedScopes,settings):
        dependencies = {}
        for scopeName,scope in self.scopeNames.items():
            if scope.isModule():
                try:
                    path = scope.resolve(root,modules,namedScopes,indexedScopes,settings)
                    if path not in modules:
                        module = np.THKModule(path,None,None,settings,external=True)
                        modules[path] = module
                        module.resolveScopeNames(modules,namedScopes,indexedScopes,settings)
                    else:
                        module = modules[path]
                    dependencies[scopeName] = module
                except SemanticError as e:
                    pass
        self.scopeMappings = dependencies
        return dependencies
    def getNodeData(self,errorlog):
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
    def mapLocalNodeNames(self,errorlog):
        nodeData = self.getNodeData(errorlog)
        variableNames = self.assignments
        unindexedNodes,indexedNodes,unidentifiedNodes,names,ids = nodeData
        idSet = set(ids.keys())
        idSet.add(0)
        self.nodeByName = names
        self.nodeByIndex = ids
        self.idGen = Autonumber(idSet)
        self.indexGen = Autonumber(indexedNodes.keys())
        self.total = max([max(indexedNodes,default = 0),len(unindexedNodes)+len(indexedNodes)],default = 0)
        for index,node in zip(self.indexGen,unindexedNodes):
            node.setIndex(index)
            indexedNodes[index] = node
        for iD,node in zip(self.idGen,unidentifiedNodes):
            node.setId(iD)
            ids[iD] = node
        for node in self.nodes:
            node.resolveImmediateCalls(indexedNodes,names,variableNames)
    def resolveInlines(self):
        for node in self.nodes:
            node.resolveInlines(self,self.scopeMappings)      
        
class ScopeTarget():
    def __init__(self,target,type):
        self.target = str(target)
        self.type = type
        #path,id,ix,local,terminal_local
    def isModule(self):
        return self.type not in ["local","terminal_local"]
    def resolve(self,root,modules,namedScopes,indexedScopes,settings):
        if self.type == "path":
            path = (root/self.target).absolute()
        elif self.type == "id":
            if self.target not in namedScopes:
                settings.compiler.missingScope(self.target)
                raise SemanticError("%s is not a scope defined within the project"%self.target)
            path = namedScopes[self.target].path
        elif self.type == "ix":
            if self.target > len(indexedScopes):
                settings.compiler.indexOverflow(self.target)
                raise SemanticError("%d exceedsd the number of thk indices"%self.target)
            if indexedScopes[self.target][0] == "":#TODO - Encapsulate the indexed scopes into objects instead of tuples
                settings.compiler.emptyScope(self.target)    
                raise SemanticError("%d is an unspecified THK on the project"%self.target)
            path = indexedScopes[self.target]
        else:
            raise SemanticError("Local and Terminal Local cannot resolve to paths.")
        self.path = path
        return path
    def __str__(self):
        return str(self.target)
class ActionTarget():
    def __init__(self,target,typing):
        self.target = target
        self.typing = typing
class Identifier():
    def __init__(self,identifier):
        self.id = identifier
    def __str__(self):
        return str(self.id)
    def resolveImmediateId(self,variableNames):
        if self.id not in variableNames:
            raise SemanticError("Variable name %s not in namespace"%(self.id))
        self.raw_id = variableNames[self.id]
class IdentifierRaw():
    def __init__(self,identifier):
        self.raw_id = identifier
    def resolveImmediateId(self,_):
        return
    def __str__(self):
        return str(self.raw_id)
class FunctionScopedId():
    def __init__(self,scope,target):
        self.scope = scope
        self.target = target
    def __str__(self):
        return str(self.scope) + "." + str(self.target)
    def resolveImmediateId(self,variableNames):
        return
class TextID(str):
    pass
class Node():
    def __init__(self,header,bodylist):
        self.header = header
        self.bodylist = bodylist
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
    def __str__(self):
        result = ""
        result += str(self.header) + "\n"
        result += ''.join((str(b) + '\n' for b in self.bodylist))
        return result
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
                if not controller.hasInlineCall(inlineCall):
                    controller.importInline(scopes[inlineCall.scope],inlineCall.target)
                node = controller.getInlineCall(inlineCall)
                segment.resolveInlineCall(node)
    def resolveTerminals(self):
        pass
                    
class NodeHeader():
    def __init__(self,aliaslist,index):
        self.names = [str(alias) for alias in aliaslist]
        self.id,self.index  = index
    def __str__(self):
        return "def " + ' & '.join(map(str,self.names)) + ":"
class Segment():
    def __init__(self):
        self._function = None
        self._call = None
        self._directive = None
        self._action = None
        self._flowControl = None
        self._randomType = None
        self._terminator = None
        self._metaparams = None
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
        self.existingCheck("flowControl")
        self._flowControl = "ConditionalStart"
    def addConditionalBranch(self):
        self.existingCheck("flowControl")
        self._flowControl = "ConditionalBranch"
    def endConditional(self):
        self.existingCheck("flowControl")
        self._flowControl = "ConditionalEnd"
    def addEnd(self):
        self.existingCheck("terminator")
        self._terminator = True
    def addChance(self,chance):
        self.existingCheck("randomType")
        self._endRandomType = "Chance"
    def endChance(self):
        self.existingCheck("flowControl")
        self._flowControl = "ChanceEnd"
    def addConclude(self):
        self.existingCheck("flowControl")
        self._flowControl = "Conclude"
    def addMeta(self,params):
        self._metaparams = params
    def substituteScopes(self,moduleScopes,actionScopes):
        for member in ["call","action"]:
            value = getattr(self,"_"+member)
            if value is not None:
                value.substituteScope(moduleScopes,actionScopes)
    def resolveImmediateCalls(self,localIndices,localNames,variableNames):
        if self._call is not None:
            self._call.immediateResolve(localIndices,localNames)
        for field in ["function"]:
            fieldVal = getattr(self,"_"+field)
            if fieldVal is not None:
                fieldVal.resolveImmediateId(variableNames)
    def __str__(self):
        return ','.join([attr if not attr == "flowControl" else self._flowControl
            for attr in ["function","call","action","directive","flowControl",
                         "randomType","terminator","metaparams"]
            if getattr(self,"_"+attr) is not None])
class Chance():
    def __init__(self,percentage):
        self.chance = percentage
class ChanceHead(Chance):
    pass
class ChanceElse(Chance):
    pass
class FunctionShell():
    def __init__(self,id,params):
        self.sections = [id]
        self.params = [params]
    def extend(self,other):
        self.sections += other.sections
        self.params += other.params
    def resolveImmediateId(self,varNames):
        for paramGroup in self.params:
            for param in paramGroup:
                try:
                    param.resolveImmediateId(varNames)
                except SemanticError:
                    pass
class FunctionLiteral():
    def __init__(self,function,arguments):
        self.function = function
        self.arguments = arguments
class Register():
    def resolveImmediateId(self,variables):
        return
class RegisterID(Register):
    def __init__(self,id):
        self.identifier = id
class RegisterComparison(Register):
    def __init__(self,ref,val,comp):
        self.base = ref
        self.target = val
        self.comparison = comp
    def resolveImmediateId(self,variables):
        self.target.resolveImmediateId(variables)
class RegisterUnaryOp(Register):
    def __init__(self,ref,op):
        self.base = ref
        self.operator = op
class Action():
    def __init__(self):
        self.parameters = []
    def addParameters(self,parameters):
        self.parameters += parameters
class ActionLiteral(Action):
    def __init__(self,id):
        self.raw_id = id
        super().__init__()
    def substituteScope(self,*arg,**kwargs):
        pass
class ActionID(Action): 
    def __init__(self,name):
        self.id = name
        super().__init__()
    def substituteScope(self,*arg,**kwargs):
        pass
class ScopedAction(Action):
    def __init__(self,scope,name):
        self.scope = str(scope)
        self.id = str(name)
        super().__init__()
    def substituteScope(self,moduleScope,actionScope):
        if self.scope in actionScope:
            self.scope = actionScope[self.scope]
        else:
            raise SemanticError("%s is not within the file's import list"%self.scope)
class Call():
    local_scope = "indices"
    def __init__(self,ix):
        self.raw_target = ix
        self.target = ix
    def immediateResolve(self,localIndices,localNames):
        self._immediateResolve(indices = localIndices, names = localNames)
    def _immediateResolve(self,**kwargs):
        if self.target not in kwargs[self.local_scope]:
            raise SemanticError("Call refers to non-existant memeber of node %s %d"%(self.local_scope,self.target))
        self.node_target = kwargs[self.local_scope][self.target]
class CallID(Call):
    local_scope = "names"
    def __init__(self,namedId):
        self.target = str(namedId)
    def substituteScope(self,*arg,**kwargs):
        pass
class ScopedCall(Call):
    def __init__(self,scope,target):
        self.scope = str(scope)
        self.target = str(target)
    def substituteScope(self,moduleScope,actionScope):
        if self.scope in moduleScope:
            self.scope = moduleScope[self.scope]
        else:
            raise SemanticError("%s is not within the file's import list"%self.scope)
    def immediateResolve(self,*args,**kwargs):
        pass
class Directive():
    def __init__(self,command):
        self.raw_target = {"return":0x8,"repeat":0x4,"reset":0x80}[command]
        