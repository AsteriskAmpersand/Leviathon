# -*- coding: utf-8 -*-
"""
Created on Thu Nov 25 04:40:09 2021

@author: Asterisk
"""
from Leviathon.compiler.errorHandler import ErrorManaged, copy


class Chance(ErrorManaged):
    subfields = ["chance"]

    def __init__(self, percentage):
        self.tag = "Stochastic Choice [%s]" % str(percentage)
        self.chance = percentage

    def copy(self):
        return Chance(self.chance)

    def resolveLocal(self, symbolsTable):
        self.chance.resolveLocal(symbolsTable,"var")

    def resolveCaller(self, namespace, assignments):
        self.chance.resolveCaller(namespace, assignments,"var")

    def resolveTerminal(self, symbolsTable):
        self.chance.resolveTerminal(symbolsTable,"var")

    def resolveProperties(self, storage):
        storage("parameter1", self.chance.getRaw())

    def __repr__(self):
        return "<Chance> " + repr(self.chance)


class ChanceHead(Chance):
    def resolveProperties(self, storage):
        storage("endRandom", 0x40)
        super().resolveProperties(storage)


class ChanceElse(Chance):
    def last(self):
        return ChanceLast(self.chance)

    def resolveProperties(self, storage):
        storage("endRandom", 0xC0)
        super().resolveProperties(storage)


class ChanceLast(Chance):
    def resolveProperties(self, storage):
        storage("endRandom", 0x80)
        super().resolveProperties(storage)
