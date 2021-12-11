# -*- coding: utf-8 -*-
"""
Created on Tue Dec  7 17:09:50 2021

@author: Asterisk
"""

sBasicUnaryOperators = ["++", "|-"]
sExtendedUnaryOperators = ["--", "##", "#-"]
sUnaryOperators = sBasicUnaryOperators + sExtendedUnaryOperators
sUnaryOperatorsMap = {op: ix for ix, op in enumerate(sUnaryOperators)}
sUnaryNames = ["INCREMENT", "CLEAR", "DECREMENT", "TIME", "ELAPSED"]

sBasicBinaryOperators = ["==", "<=", "<", ">=", ">", "!="]
sExtendedBinaryOperators = [":=", "+=", "-=", "*=", "/=", "%=","<:=","=:>"]
sTemporalBinaryOperators = ["#>", "#<"]
sBinaryNames = ["EQ", "LEQ", "LT", "GEQ", "GT", "NEQ", "SET",
                "ADD", "SUB", "MUL", "DIV", "MOD", "PTRGET", "PTRSET", "ELAPGT", "ELAPLT"]

sBinaryOperators = sBasicBinaryOperators + \
    sExtendedBinaryOperators + sTemporalBinaryOperators
sBinaryOperatorsMap = {op: ix for ix, op in enumerate(sBinaryOperators)}

monstersUnary = {0xa8: 20, 0xaa: 21}
monstersBinary = {0xa9: 20, 0xab: 21}


def getRegisterIndex(segment):
    functionID = segment.functionType
    if 0x80 <= functionID <= 0x93:
        return functionID - 0x80
    elif functionID in monstersUnary:
        return monstersUnary[functionID]
    elif functionID in monstersBinary:
        return monstersBinary[functionID]
    else:
        return functionID-0x94


def getRegisterFunction(regIndex, Operator):
    pass


def getRegisterOperator(segment):
    if isUnary(segment):
        return sUnaryOperators[segment.parameter1]
    else:
        return sBinaryOperators[segment.parameter1 % len(sBinaryOperators)]


def isUnary(segment):
    if 0x80 <= segment.functionType <= 0x93 \
            or segment.functionType in monstersUnary:
        return True
    else:
        return False


def isExternal(segment):
    return segment.parameter1 >= len(sBinaryOperators)


def isRegister(segment):
    return 0x80 <= segment.functionType <= 0xab


def unaryIndex(index):
    if index > 19:
        return 0xa8 + (index-20)*2
    else:
        return 0x80 + index


def binaryIndex(index):
    if index > 19:
        return 0xa9 + (index-20)*2
    else:
        return 0x94 + index
# sUnaryOperators[segment.parameter1]
# sBinaryOperators[segment.parameter1]


def registerResolve(segment, registerScheduler):
    segment.log("functionType")
    segment.log("parameter1")
    registerName = registerScheduler.resolve(getRegisterIndex(segment))
    op = getRegisterOperator(segment)
    if isUnary(segment):
        return "[%s %s]" % (registerName, op)
    else:
        segment.log("parameter2")
        if isExternal(segment):
            target = registerScheduler.resolve(segment.parameter2)
        else:
            target = str(segment.parameter2)
        return "[%s %s %s]" % (registerName, op, target)
