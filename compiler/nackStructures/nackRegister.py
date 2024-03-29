# -*- coding: utf-8 -*-
"""
Created on Thu Nov 25 04:42:16 2021

@author: Asterisk
"""
from compiler.errorHandler import ErrorManaged, copy
from common.registerOperations import sUnaryOperatorsMap, sBinaryOperatorsMap,\
    unaryIndex, binaryIndex


class Register():
    def resolveLocal(self, symbolsTable):
        pass

    def resolveScopedAssignments(self, scope, assignments):
        pass

    def resolveCaller(self, namespace, assignments):
        pass

    def resolveTerminal(self, symbolsTable):
        pass

    def resolveName(self, registerNamespace):
        if self.raw_id is not None:
            return
        self.raw_id = registerNamespace[self.identifier]

    def collectRegisters(self):
        if self.raw_id is not None:
            return [self.raw_id]
        else:
            return [str(self.identifier)]

    def __repr__(self):
        ide = repr(self.identifier)
        return "<Reg> %s" % ide


class RegisterID(Register, ErrorManaged):
    tag = "Register ID"
    subfields = ["identifier"]

    def __init__(self, id):
        self.tag = "Register ID [%s]" % (id)
        self.identifier = id
        self.raw_id = None

    def copy(self):
        return RegisterID(copy(self.identifier))


class RegisterLiteral(Register, ErrorManaged):
    tag = "Register Literal"
    subfields = ["identifier"]

    def __init__(self, id):
        self.tag = "Register ID [%s]" % (id)
        self.identifier = id
        self.raw_id = id

    def copy(self):
        return RegisterID(copy(self.identifier))


class RegisterOp():
    typing = "register"

    def resolveLocal(self, varNames):
        pass

    def resolveScopedAssignments(self, scope, namespace):
        pass

    def resolveCaller(self, namespace, assignments):
        pass

    def resolveTerminal(self, symbolsTable):
        pass

    def resolveName(self, namespace):
        self.base.resolveName(namespace)

    def collectRegisters(self):
        return self.base.collectRegisters()


class RegisterComparison(RegisterOp, ErrorManaged):
    subfields = ["base", "target", "comparison"]

    def __init__(self, ref, val, comp):
        self.invert = False
        self.tag = "Register Comparison [%s %s %s]" % (ref, comp, val)
        self.base = ref
        self.target = val
        self.comparison = comp

    def copy(self):
        newReg = type(self)(copy(self.base),
                            copy(self.target),
                            copy(self.comparison))
        newReg.invert = self.invert
        return newReg

    def resolveNames(self, operator, *args):
        getattr(self.target, operator)(*args, "var")

    def resolveLocal(self, symbolsTable):
        self.resolveNames("resolveLocal", symbolsTable)

    def resolveScopedAssignments(self, scope, assignments):
        self.resolveNames("resolveScopedAssignments", scope, assignments)

    def resolveCaller(self, namespace, assignments):
        self.resolveNames("resolveCaller", namespace, assignments)

    def resolveTerminal(self, symbolsTable):
        self.resolveNames("resolveTerminal", symbolsTable)

    def resolveProperties(self, storage):
        if self.base.raw_id is None:
            self.errorHandler.unresolvedIdentifier(str(self.base))
        print(self.invert)
        ft = [1,-1][self.invert]*binaryIndex(self.base.raw_id)
        storage("functionType",ft)
        storage("parameter1", sBinaryOperatorsMap[self.comparison])
        storage("parameter2", self.target.getRaw())

    def __repr__(self):
        return "<RegComp> %s %s %s" % tuple(map(repr, (self.base,
                                                       self.comparison,
                                                       self.target)))


class RegisterExtendedComparison(RegisterComparison):
    subfields = ["base", "target", "comparison", "extended"]

    def __init__(self, *args, **kwargs):
        self.extended = False
        super().__init__(*args, **kwargs)

    def copy(self):
        new = super().copy()
        new.extended = self.extended
        return new

    def extendTarget(self):
        try:
            extended = RegisterID(self.target.id)
            self.inheritChildren(extended)
            self.target = extended
            self.extended = True
        except AttributeError:
            self.errorHandler.unresolvedScopeInRegister(
                "%s.%s" % (self.target.scope, self.target.target))
            raise

    def collectRegisters(self):
        if self.target.raw_id is None:
            try:
                self.extendTarget()
            except:
                return []
            return self.base.collectRegisters() + self.target.collectRegisters()
        return self.base.collectRegisters()

    def resolveName(self, namespace):
        if self.extended:
            self.target.resolveName(namespace)
        self.base.resolveName(namespace)

    def resolveProperties(self, storage):
        if self.base.raw_id is None:
            self.errorHandler.unresolvedIdentifier(str(self.base))
        if self.target.raw_id is None:
            self.errorHandler.unresolvedIdentifier(str(self.target))
        if self.extended:
            param1Offset = len(sBinaryOperatorsMap)
            target =self.target.raw_id
        else:
            param1Offset = 0
            target = self.target.getRaw()
        storage("functionType", [1,-1][self.invert]*(binaryIndex(self.base.raw_id)))
        storage("parameter1",
                sBinaryOperatorsMap[self.comparison] + param1Offset)
        storage("parameter2", target)


class RegisterUnaryOp(RegisterOp, ErrorManaged):
    tag = "Register Unary Operator"
    subfields = ["base", "operator"]

    def __init__(self, ref, op):
        self.invert = False
        self.tag = "Register Unary [%s %s]" % (ref, op)
        self.base = ref
        self.operator = op

    def copy(self):
        return RegisterUnaryOp(copy(self.base), copy(self.operator))

    def resolveProperties(self, storage):
        if self.base.raw_id is None:
            self.errorHandler.unresolvedIdentifier(str(self.base))
        else:
            storage("functionType", [1,-1][self.invert]*unaryIndex(self.base.raw_id))
            storage("parameter1", sUnaryOperatorsMap[self.operator])

    def __repr__(self):
        return "<RegComp> %s %s" % tuple(map(repr, (self.base,
                                                    self.operator,)))