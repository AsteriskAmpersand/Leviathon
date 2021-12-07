# -*- coding: utf-8 -*-
"""
Created on Thu Nov 25 04:45:36 2021

@author: Asterisk
"""
from compiler.errorHandler import ErrorManaged, copy

# if not hasattr(self.id, "raw_id"):
#    self.errorHandler.unresolvedIdentifier(self.id)
#    return

#typing = var, node, action, register


class IdClass():
    def getRaw(self):
        if self.raw_id is None:
            self.errorHandler.unresolvedIdentifier(self.id)
        return self.raw_id

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
        return self

    def __str__(self):
        if self.raw_id is not None:
            return str(self.raw_id)
        return str(self.id)

    def __repr__(self):
        status = "<ID> " + str(self.id)
        if self.raw_id is not None:
            status = "<R-ID> " + str(self.id) + " [" + str(self.raw_id) + "]"
        if self.node_target is not None:
            status += " {-> %s}" % (self.node_target.names()[0])
        return status

    def literal(self):
        if self.raw_id:
            return str(self.raw_id)
        else:
            return self.id


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

    def sequelize(self, omit=False):
        nid = Identifier((self.scope+"::" if not omit else "")+self.target)
        nid.raw_id = self.raw_id
        nid.node_target = self.node_target
        nid.module = self.module
        return nid

    def resolveLocal(self, symbolsTable, typing):
        if self.scope not in ["Caller", "Terminal"]:
            result = symbolsTable.resolveScope(self.scope)
            if typing == "node" and result:
                self.module = result
                return self.resolveCall()
            return result

    def resolveCaller(self, namespaces, variables, typing):
        if typing != "node":
            if self.raw_id is not None:
                return self.raw_id
            if self.scope in namespaces:
                if self.target in variables:
                    self.raw_id = variables[self.target]
                    return self.raw_id
        else:
            if self.scope in namespaces:
                namespace = namespaces[self.scope]
                if self.target in namespace:
                    self.node_target = namespace[self.target]
                    return self.node_target

    def resolveTerminal(self, symbolsTable, typing):
        if self.raw_id is not None:
            return self.raw_id
        if self.node_target is not None:
            return self.node_target
        if self.scope == "Terminal":
            resolution = symbolsTable.resolve(self.target, typing)
            if typing == "node":
                self.node_target = resolution
                self.module = symbolsTable.parent
                return self.node_target
            else:
                self.raw_id = resolution
                return self.raw_id
        return

    def resolveCall(self):
        return self.module.resolveFunction(self.target)

    def copy(self):
        nid = IdentifierScoped(copy(self.scope), copy(self.target))
        nid.raw_id = self.raw_id
        nid.module = self.module
        nid.node_target = self.node_target
        return nid

    def verifyEnum(self, enumManager):
        return str(self.scope) == enumManager.scope() and str(self.target) in enumManager

    def accessEnum(self, enumManager):
        return enumManager[str(self.target)].getId()

    def __repr__(self):
        sol = self.scope + "." + self.target
        status = "<SID> " + sol
        if self.raw_id is not None:
            status = "<R-SID> " + sol + " [" + str(self.raw_id) + "]"
        if self.node_target is not None:
            status += " {-> %s}" % self.node_target.names()[0]
        return status

    def __str__(self):
        if self.raw_id:
            return str(self.raw_id)
        else:
            return self.scope + "." + self.target


class TextID(str, IdClass, ErrorManaged):
    tag = "Text ID"
    subfields = []

    def copy(self):
        return TextID(self)

    def __str__(self):
        return self
