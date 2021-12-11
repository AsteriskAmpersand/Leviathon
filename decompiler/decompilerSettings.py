# -*- coding: utf-8 -*-
"""
Created on Sun Oct 31 01:18:07 2021

@author: Asterisk
"""


class DecompilerSettings():
    def __init__(self):
        self.keepVoid = False
        self.keepLast = False
        self.genPlaceholder = False
        self.forceIndex = False
        self.forceId = False
        self.listCrossreferences = False
        self.disableActionMapping = False

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
