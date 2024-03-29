# -*- coding: utf-8 -*-
"""
Created on Thu Nov 25 04:40:09 2021

@author: Asterisk
"""
from compiler.errorHandler import ErrorManaged, copy


class Chance(ErrorManaged):
    subfields = ["chance"]

    def __init__(self, percentage, code = None):
        self.tag = "Stochastic Choice [%s]" % str(percentage)
        self.chance = percentage
        self.code = self.codeClass if code is None else code

    def copy(self):
        newChance = type(self)(copy(self.chance),self.code)
        return newChance

    def resolveLocal(self, symbolsTable):
        self.chance.resolveLocal(symbolsTable, "var")

    def resolveScopedAssignments(self, scope, assignments):
        self.chance.resolveScopedAssignments(scope, assignments, "var")

    def resolveCaller(self, namespace, assignments):
        self.chance.resolveCaller(namespace, assignments, "var")

    def resolveTerminal(self, symbolsTable):
        self.chance.resolveTerminal(symbolsTable, "var")

    def resolveProperties(self, storage):
        storage("endRandom", self.code)
        storage("parameter1", self.chance.getRaw())

    def __repr__(self):
        signum = {0x40: "H-", 0xC0: "E-", 0x80: "L-"}[self.code]
        return "<%sRandom> " % signum + repr(self.chance)


class ChanceHead(Chance):
    codeClass = 0x40


class ChanceElse(Chance):
    codeClass = 0xC0

    def last(self):
        self.code = 0x80