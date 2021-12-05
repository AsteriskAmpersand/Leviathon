# -*- coding: utf-8 -*-
"""
Created on Thu Nov 25 04:43:01 2021

@author: Asterisk
"""
from compiler.errorHandler import ErrorManaged, copy


class Call(ErrorManaged):
    subfields = ["target"]
    local_scope = "getIndex"

    def __init__(self, ix):
        self.tag = "Call [%s]" % str(ix)
        self.target = ix
        self.node_target = None
        self.raw_target = ix
        self.external = -1

    def resolveNames(self, operator, *args):
        if self.node_target or self.raw_target: return
        self.node_target = getattr(self.target,operator)(*args,"node")

    def resolveLocal(self, symbolsTable):
        self.resolveNames("resolveLocal", symbolsTable)

    def resolveCaller(self, namespace, assignments):
        return self
    
    def resolveTerminal(self, symbolsTable):
        return self

    def resolveCalls(self):
        if self.raw_target is not None: return self.raw_target
        self.raw_target = getattr(self.node_target,self.local_scope)()
        self.external = -1
        self.target.raw_id = self.raw_target
            
    def reconnectChain(self,target):
        self.node_target = target
        self.target.node_target = target
        return self

    def internalCall(self):
        return True

    def inlineCall(self):
        return False

    def copy(self):
        c = type(self)(copy(self.target))
        c.node_target = self.node_target
        c.raw_target = self.raw_target
        c.external = self.external
        return c

    def resolveProperties(self, storage):
        if not hasattr(self, "raw_target"):
            self.errorHandler.unresolvedIdentifier()
        else:
            if self.external == -1:
                storage("extRefThkID", self.external)
                storage("extRefNodeID", self.external)
                storage("localRefNodeID", self.raw_target)
            else:
                storage("extRefThkID", self.external)
                storage("extRefNodeID", self.raw_target)
                storage("localRefNodeID", -1)

    def __repr__(self):
        return "<Call> " + repr(self.target)


class CallID(Call):
    local_scope = "getIndex"

    def __init__(self, namedId):
        self.tag = "Call ID [%s]" % namedId
        self.target = namedId
        self.node_target = None
        self.raw_target = None
        self.external = None


class ScopedCallID(Call):
    subfields = ["target"]
    local_scope = "getId"

    def __init__(self, target):
        self.tag = "Call Scoped ID [%s]" % (target)
        self.target = target
        self.node_target = None
        self.raw_target = None
        self.external = None

    def internalCall(self):
        return False

    def inlineCall(self):
        if self.target.module and self.target.module.inlineCall:
            return self.target.scope, self.target
        else:
            return False

    def copy(self):
        sc = type(self)(copy(self.target))
        sc.node_target = self.node_target
        sc.raw_target = self.raw_target
        return sc

    def resolveCalls(self):
        if self.raw_target is not None: return self.raw_target
        try:
            self.raw_target = self.node_target.getId()
            self.target.raw_id = self.raw_target
        except:
            self.errorHandler.missingNodeName(self.target)
        self.external = self.target.module.id
        
    def retarget(self,name,target):
        cnid = Call(name)
        cnid.target.node_target = target
        cnid.node_target = target
        cnid.external = -1
        cnid.raw_target = self.raw_target
        return cnid
        
    def reconnectChain(self,target):
        return self.retarget(self.target.sequelize(),target)
        
    def resolveCaller(self, namespace, assignments):
        if self.node_target or self.raw_target: return self
        newTarget = self.target.resolveCaller(namespace,assignments,"node")
        if self.target.scope in namespace and newTarget:
            return self.retarget(self.target.sequelize(omit=True),newTarget)
        else:
            return self
        
    def resolveTerminal(self,symbolsTable):
        namespace = {"Terminal":symbolsTable.nodes}
        assignments = symbolsTable.vars
        if self.node_target or self.raw_target: return self
        newTarget = self.target.resolveCaller(namespace,assignments,"node")
        if self.target.scope in namespace and newTarget:
            return self.retarget(self.target.sequelize(omit=True),newTarget)
        else:
            return self

class ScopedCall(Call):
    def __init__(self, scope,literalTarget):
        self.tag = "Call Scoped Literal [%s.%d]"%(scope,literalTarget)
        self.target = scope
        self.node_target = None
        self.raw_target = literalTarget
        self.external = None
        
    def resolveLocal(self,symbolsTable):
        self.module = symbolsTable.resolveScope(self.target)
        if self.module is None:
            self.errorHandler.missingScope(self.target)
        self.external = self.module.id

    def __repr__(self):
        return "<Call> " + repr(self.target) + " [%d]"%self.raw_target