# -*- coding: utf-8 -*-
"""
Created on Thu Nov 25 04:43:01 2021

@author: Asterisk
"""
from errorHandler import ErrorManaged,copy

class Call(ErrorManaged):
    subfields = ["target"]
    local_scope = "getIndex"
    def __init__(self,ix):
        self.tag = "Call [%s]"%str(ix)
        self.target = ix
    def resolveCalls(self):
        if hasattr(self,"raw_target"):
            return
        self.raw_target = self.node_target.getId()
        self.external = -1
    def resolveNames(self,symbolsTable,terminal = False):
        try:
            self.node_target = self.target.resolveNames(symbolsTable)
            if terminal:
                if self.target.inlined():
                    self.raw_target = self.node_target.getIndex()
                else:
                    self.raw_target = self.node_target.getID()
        except:
            pass
    def resolveLocal(self,symbolsTable):
        self.resolveNames(symbolsTable)
    def resolveCaller(self,symbolsTable):
        self.resolveNames(symbolsTable)
    def resolveTerminal(self,symbolsTable):
        self.resolveNames(symbolsTable,terminal = True)  
    def internalCall(self):
        return True
    def inlineCall(self):
        return False
    def inlinedCallerCallScopeResolution(self,_,__):
        pass
    def resolveScopeToModule(self,modulelist):
        pass
    def copy(self):
        c = Call(copy(self.target))
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
    subfields = ["target"]
    def __init__(self,target):
        self.tag = "Call Scoped ID [%s]"%(target)
        self.target = target
        #self.target = str(target)
        self.node_target = None
    def copy(self):
        c = super().copy()
        c.module = self.module
        #if self.scope.type == typing:
        #    if self.target in callerNames: self.node_target = callerNames[self.target]
        #    else: self.errorHandler.missingNodeName(self.target,str(self.scope))
    def resolveLocal(self,symbolsTable):
        self.resolveNames(symbolsTable)
    def resolveCaller(self,symbolsTable):
        self.resolveNames(symbolsTable)
    def resolveTerminal(self,symbolsTable):
        self.resolveNames(symbolsTable,terminal = True)  
    def resolveScopeToModule(self,modulelist):
        module = self.scope.resolveScopeToModule(modulelist)
        self.module = module
    def inlinedCallerCallScopeResolution(self,indices,namespaces):
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
            self.raw_target = self.module.getNodeByName(self.target).getId()
        except:
            self.errorHandler.missingNodeName(self.target)
        self.external = self.module.id
class ScopedCall(ScopedCallID):
    tag = "Call Scoped Literal"
    def resolveCalls(self):
        if hasattr(self,"raw_target"):
            return
        self.raw_target = self.target
        self.external = self.module.id