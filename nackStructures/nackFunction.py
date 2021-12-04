# -*- coding: utf-8 -*-
"""
Created on Thu Nov 25 04:41:21 2021

@author: Asterisk
"""
from errorHandler import ErrorManaged, copy


class FunctionLiteral(ErrorManaged):
    typing = "function"
    subfields = ["function", "arguments"]

    def __init__(self, function, arguments):
        self.tag = "Function Call Literal [%X]" % function
        self.function = function
        self.raw_id = function
        self.arguments = arguments

    def copy(self):
        return FunctionLiteral(copy(self.function), [copy(arg) for arg in self.arguments])

    def resolveProperties(self, storage):
        storage("functionType", self.raw_id)
        for field, parameterObj in zip(["parameter1", "parameter2"], self.arguments):
            storage(field, parameterObj.getRaw())

    def resolveFunctions(self, _):
        pass

    def resolveNames(self, operator, *args):
        for paramGroup in self.params:
            for param in paramGroup:
                getattr(param, operator)(*args, "var")

    def resolveLocal(self, symbolsTable):
        self.resolveNames("resolveLocal", symbolsTable )

    def resolveCaller(self, namespaces, assignments):
        self.resolveNames("resolveCaller", namespaces, assignments )

    def resolveTerminal(self, symbolsTable):
        self.resolveNames("resolveTerminal", symbolsTable)
        
    def __repr__(self):
        return "<FuncL> %s (%s)"%(self.function,', '.join(map(repr,self.arguments)))


class FunctionShell(FunctionLiteral, ErrorManaged):
    typing = "function"
    subfields = ["sections", "params"]

    def __init__(self, id=None, params=None):
        if id is None:
            self.tag = "Function Call Name"
            self.sections = []
            self.params = []
        else:
            self.tag = "Function Call Name [%s]" % id
            self.sections = [id]
            self.params = [params]

    def extend(self, other):
        self.sections += other.sections
        self.params += other.params

    def copy(self):
        shell = FunctionShell()
        shell.sections = [copy(id) for id in self.sections]
        shell.params = [[copy(p) for p in params] for params in self.params]
        return shell

    def resolveProperties(self, storage):
        for field, parameterValue in self.functionParamPairs:
            storage(field, parameterValue)

    def resolveFunctions(self, functionResolver):
        parameters = {}
        def testAdd(propertyName, propertyValue):
            if propertyName in parameters:
                self.errorHandler.repeatedProperty(propertyName)
            parameters[propertyName] = propertyValue
        functionResolver(self, testAdd)
        self.functionParamPairs = list(parameters.items())

    def signature(self):
        sig = []
        for literal, param in zip(self.sections, self.params):
            sig.append(-1)
            if type(param) is not str:
                sig.append(len(param))
        return tuple(sig)

    def literalSignature(self):
        return tuple(map(str, self.sections))

    def __repr__(self):
        return "<Func> %s (%s)" % (' || '.join(map(repr,self.sections)),
                                 ' || '.join(map(lambda x: ','.join(map(repr,x)),self.params)))