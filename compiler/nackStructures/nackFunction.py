# -*- coding: utf-8 -*-
"""
Created on Thu Nov 25 04:41:21 2021

@author: Asterisk
"""
from compiler.errorHandler import ErrorManaged, copy


class FunctionLiteral(ErrorManaged):
    typing = "function"
    subfields = ["function", "params"]

    def __init__(self, function, arguments):
        self.invert = False
        self.tag = "Function Call Literal [%X]" % function
        self.function = function
        self.raw_id = function
        self.params = arguments

    def copy(self):
        literal = FunctionLiteral(copy(self.function), copy(self.params))
        literal.invert = self.invert
        return literal

    def resolveProperties(self, storage):
        storage("functionType", self.raw_id if not self.invert else -self.raw_id)
        for field, parameterObj in zip(["parameter1", "parameter2"], self.params):
            storage(field, parameterObj.getRaw())

    def resolveFunctions(self, _):
        pass

    def resolveNames(self, operator, *args):
        for param in self.params:
            getattr(param, operator)(*args, "var")

    def resolveLocal(self, symbolsTable):
        self.resolveNames("resolveLocal", symbolsTable)

    def resolveCaller(self, namespaces, assignments):
        self.resolveNames("resolveCaller", namespaces, assignments)

    def resolveTerminal(self, symbolsTable):
        self.resolveNames("resolveTerminal", symbolsTable)

    def __repr__(self):
        return "<FuncL> %s (%s)" % (self.function, ', '.join(map(repr, self.params)))


class FunctionShell(FunctionLiteral, ErrorManaged):
    typing = "function"
    subfields = ["sections", "params"]

    def __init__(self, id=None, params=None):
        self.invert = False
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
        shell.invert = self.invert
        return shell

    def resolveNames(self, operator, *args):
        for paramGroup in self.params:
            for param in paramGroup:
                getattr(param, operator)(*args, "var")

    def resolveProperties(self, storage):
        for field, parameterValue in self.functionParamPairs:
            if self.invert and field == "functionType":
                parameterValue = -parameterValue
            storage(field, parameterValue)

    def resolveFunctions(self, functionResolver):
        parameters = {}

        def testAdd(propertyName, propertyValue):
            if propertyName in parameters:
                self.errorHandler.repeatedProperty(propertyName)
            parameters[propertyName] = propertyValue
        try:
            functionResolver(self, testAdd)
        except:
            self.errorHandler.unmatchedFunctionSignature(self.errorRepr())
            return
        self.functionParamPairs = list(parameters.items())

    def getParameters(self):
        return [param for param in self.params if type(param) is not str]

    def signature(self):
        sig = []
        for literal, param in zip(self.sections, self.params):
            sig.append(-1)
            if type(param) is not str:
                sig.append(len(param))
        return tuple(sig)

    def literalSignature(self):
        return tuple(map(str, self.sections))

    def errorRepr(self):
        result = "self."
        result += ".".join([literal + "(" + arg + ")"
                            for literal, arg in zip(map(str, self.sections),
                                                    map(lambda x: ','.join(map(str, x)), self.params))])

        return result

    def __repr__(self):
        return "<Func> %s (%s)" % (' || '.join(map(repr, self.sections)),
                                   ' || '.join(map(lambda x: ','.join(map(repr, x)), self.params)))

def NegatedFunction(pureFunction):
    pureFunction.invert = True
    return pureFunction