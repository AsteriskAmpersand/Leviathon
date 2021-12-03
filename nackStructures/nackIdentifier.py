# -*- coding: utf-8 -*-
"""
Created on Thu Nov 25 04:45:36 2021

@author: Asterisk
"""
from errorHandler import ErrorManaged, copy

# if not hasattr(self.id, "raw_id"):
#    self.errorHandler.unresolvedIdentifier(self.id)
#    return

#typing = var, node, action, register


class IdClass():
    def resolveLocal(self, symbolsTable, typing):
        if typing != "node":
            if self.raw_id is not None:
                return self.raw_id
            self.raw_id = symbolsTable.resolve(self.id, typing)
            return self.raw_id
        else:
            if self.node_target:
                return self.node_target
            self.node_target = symbolsTable.resolve(self.id, typing)
            return self.node_target

    def resolveCaller(self, namespace, assignments, typing):
        return self.raw_id

    def resolveTerminal(self, symbolsTable, typing):
        if typing == "node" and self.raw_id is None and self.node_target:
            self.resolveLocal(symbolsTable,typing)
        if typing == "node":
            if not self.node_target:
                self.error.missingCallTarget(self.id)
                return -1
            return self.node_target.getIndex()
        else:
            return self.raw_id
    
    def __str__(self):
        status = "<ID> " + str(self.id)
        if self.raw_id is not None:
            status = "<R-ID> " + str(self.id) + " [" + str(self.raw_id) + "]"
        if self.node_target is not None:
            status += " {-> %s}"%(self.node_target.names()[0])
        return status
        
# self.errorHandler.missingVariableName(self.id)


class Identifier(IdClass, ErrorManaged):
    subfields = ["id"]

    def __init__(self, identifier):
        self.tag = "Identifier [%s]" % str(identifier)
        self.id = identifier
        self.raw_id = None
        self.node_target = None

    def copy(self):
        nid = Identifier(copy(self.id))
        nid.raw_id = self.raw_id
        return nid

    def verifyEnum(self, _):
        return False


class IdentifierRaw(IdClass, ErrorManaged):
    subfields = ["raw_id"]

    def __init__(self, identifier):
        self.tag = "Identifier Literal [%s]" % str(identifier)
        self.id = identifier
        self.raw_id = identifier
        self.node_target = None

    def copy(self):
        return IdentifierRaw(copy(self.raw_id))

    def verifyEnum(self, enumManager):
        return self.raw_id in enumManager

    def accessEnum(self, enumManager):
        return self.raw_id


class IdentifierScoped(IdClass, ErrorManaged):
    tag = "Function Scoped ID"
    subfields = ["target", "scope"]

    def __init__(self, scope, target):
        self.scope = str(scope)
        self.target = str(target)
        self.raw_id = None
        self.module = None
        self.node_target = None

    def sequelize(self,omit = False):
        nid = Identifier((self.scope+"::" if not omit else "")+self.target)
        nid.raw_id = self.raw_id
        nid.node_target = self.node_target
        nid.module = self.module
        return nid

    def resolveLocal(self, symbolsTable, typing):
        if self.scope not in ["Caller", "Terminal"]:
            self.module = symbolsTable.resolveScope(self.scope)
            return self.module

    def resolveCaller(self, namespaces, variables, typing):
        if typing != "node":
            if self.scope in namespaces:
                if self.target in variables:
                    self.raw_id = variables[self.target]
        else:
            if self.scope in namespaces:
                namespace = namespaces[self.scope]
                if self.target in namespace:
                    self.node_target = namespace[self.target]
                    return self.node_target

    def resolveTerminal(self, symbolsTable, typing):
        if self.scope == "Terminal":
            resolution = symbolsTable.resolve(self.target,typing)
            if typing == "node":
                self.node_target = resolution
            else:
                self.raw_id = resolution
                #TODO
        #super().resolveTerminal(self,symbolsTable,typing)
        return 
        

    def copy(self):
        nid = IdentifierScoped(copy(self.scope), copy(self.target))
        nid.raw_id = self.raw_id
        nid.module = self.module
        nid.node_target = self.node_target
        return nid

    def verifyEnum(self, enumManager):
        return str(self.scope) == enumManager.scope and str(self.target) in enumManager

    def accessEnum(self, enumManager):
        return enumManager[str(self.target)]
    
    def __str__(self):
        sol = self.scope + "." + self.target
        status = "<SID> " + sol
        if self.raw_id is not None:
            status = "<R-SID> " + sol + " [" + str(self.raw_id) + "]"
        if self.node_target is not None:
            status += " {->}"
        return status


class TextID(str, IdClass, ErrorManaged):
    tag = "Text ID"
    subfields = []

    def copy(self):
        return TextID(self)
