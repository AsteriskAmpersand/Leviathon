# -*- coding: utf-8 -*-
"""
Created on Thu Nov 25 04:45:36 2021

@author: Asterisk
"""
from errorHandler import ErrorManaged,copy

class Identifier(ErrorManaged):
    subfields = ["id"]
    def __init__(self,identifier):
        self.tag = "Identifier [%s]"%str(identifier)
        self.id = identifier
    def __str__(self):
        return str(self.id)
    
    def resolveCallerId(self,variableNames):
        pass
    def resolveTerminalId(self,variableNames):
        pass
    def resolveImmediateId(self,variableNames):
        if self.id not in variableNames:
            self.errorHandler.missingVariableName(self.id)
        self.raw_id = variableNames[self.id]
    def copy(self):
        return Identifier(copy(self.id))
    def verifyEnum(self,_):
        return False
class IdentifierRaw(ErrorManaged):
    subfields = ["raw_id"]
    def __init__(self,identifier):
        self.tag = "Identifier Literal [%s]"%str(identifier)
        self.raw_id = identifier
    def resolveImmediateId(self,_):
        return
    def resolveTerminalId(self,variableNames):
        pass
    def resolveCallerId(self,variableNames):
        pass
    def __str__(self):
        return str(self.raw_id)
    def copy(self):
        return IdentifierRaw(copy(self.raw_id))
    def verifyEnum(self,enumManager):
        return self.raw_id in enumManager
    def accessEnum(self,enumManager):
        return self.raw_id
class IdentifierScoped(ErrorManaged):
    tag = "Function Scoped ID"
    subfields = ["target","scope"]
    def __init__(self,scope,target):
        self.scope = scope
        self.target = target
    def __str__(self):
        return str(self.scope) + "." + str(self.target)
    def scopeResolve(self,variableNames,typing):
        if str(self.scope) == typing:
            if self.target in variableNames:
                self.raw_id = variableNames[self.target]
            else:
                self.errorHandler.missingNodeName(self.target,str(self.scope))
    def resolveCallerId(self,variableNames):
        self.scopeResolve(variableNames,"Caller")
    def resolveTerminalId(self,variableNames):
        self.scopeResolve(variableNames,"Terminal_Caller")
    def resolveImmediateId(self,variableNames):
        return
    def copy(self):
        return IdentifierScoped(copy(self.scope),copy(self.target))
    def verifyEnum(self,enumManager):
        return str(self.scope) == enumManager.scope and str(self.target) in enumManager
    def accessEnum(self,enumManager):
        return enumManager[str(self.target)]
class TextID(str,ErrorManaged):
    tag = "Text ID"
    subfields = []
    def copy(self):
        return TextID(self)