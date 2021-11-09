# -*- coding: utf-8 -*-
"""
Created on Sun Oct 31 01:18:07 2021

@author: Asterisk
"""

class DecompilerSettings():
    def __init__(self):
        self.keepVoid = False
        self.keepLast = False
        self.forceIndex = False
        self.forceId = False
        self.listCrossreferences = False

        self.raiseInvalidReference = False
        self.suppressWarnings = False
        self.keepRegisters = False
        self.forceRegisters = False
        self.functionAsThkName = False

        self.verbose = False
        self.display = print
        self.runCodeAnalysis = False

        self.outputPath = None
        self.statisticsOutputPath = None


class CompilerSettings():
    def __init__(self):
        self.verbose = False
        self.display = print
        
        self.entityMap = None
        self.root = None
        self.thkMap = None
        self.inlineForeign = False
        self.foreignGlobal = False


class TranspilerSettings():
    def __init__(self):
        self.decompiler = DecompilerSettings()
        self.compiler = CompilerSettings()