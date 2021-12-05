# -*- coding: utf-8 -*-
"""
Created on Thu Nov 25 04:36:58 2021

@author: Asterisk
"""

from Leviathon.compiler.errorHandler import ErrorManaged, copy


class Action(ErrorManaged):
    tag = "Action"
    subfields = ["parameters"]

    def __init__(self):
        self.raw_id = None
        self.parameters = []

    def addParameters(self, parameters):
        self.parameters += parameters

    def copy(self, *args, **kwargs):
        a = type(self)(*args, **kwargs)
        a.parameters = [copy(p) for p in self.parameters]
        return a

    def resolveNames(self, operator, *args):
        for param in self.parameters:
            getattr(param, operator)(*args, "var")

    def resolveLocal(self, symbolsTable):
        self.resolveNames("resolveLocal", symbolsTable)

    def resolveCaller(self, namespaces, assignments):
        self.resolveNames("resolveCaller", namespaces, assignments)

    def resolveTerminal(self, symbolsTable):
        self.resolveNames("resolveTerminal", symbolsTable)

    def resolveProperties(self, storage):
        if not hasattr(self, "raw_id"):
            self.errorHandler.unresolvedIdentifier()
        else:
            storage("actionID", self.raw_id)
            for ix, param in enumerate(self.parameters):
                if ix >= 5:
                    param.errorHandler.actionParameterCountExceeded(ix)
                    continue
                if hasattr(param, "raw_id"):
                    storage("actionUnkn%d" % ix, param.getRaw())
                else:
                    param.errorHandler.unresolvedIdentifier()

    def resolved(self,resolution):
        self.raw_id = resolution
        self.id.raw_id = resolution
        return resolution

    def __repr__(self):
        identifier = self.id if self.raw_id is None else self.raw_id
        return "<Action> [%s]"%repr(identifier)+"("+\
                ','.join(map(repr,self.parameters))+")"


class ActionLiteral(Action):
    def __init__(self, id):
        self.tag = "Action Literal [%d]" % id
        self.id = id
        self.raw_id = id
        super().__init__()

    def resolveAction(self, _):
        super.resolved(self.raw_id)
        return self.raw_id

    def copy(self):
        return super().copy(copy(self.raw_id))


class ActionID(Action):
    subfields = ["parameters", "id"]

    def __init__(self, name):
        self.tag = "Action ID [%s]" % name
        self.id = name
        self.raw_id = None
        super().__init__()

    def resolveAction(self, actionScopes):
        resolution = actionScopes["monster"].resolveAction(self.id.id)
        super().resolved(resolution)
        return resolution

    def copy(self):
        return super().copy(copy(self.id))

class ScopedAction(ActionID):
    def resolveAction(self, actionScopes):
        if self.id.scope not in actionScopes:
            self.errorHandler.missingActionScope(self.id.scope)
            resolution = -1
        else:
            resolution = actionScopes[self.id.scope].resolveAction(self.id.target)
        super().resolved(resolution)
        return resolution