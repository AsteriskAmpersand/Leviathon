# -*- coding: utf-8 -*-
"""
Created on Thu Nov 25 04:36:58 2021

@author: Asterisk
"""

from errorHandler import ErrorManaged,copy

class Action(ErrorManaged):
    tag = "Action"
    subfields = ["parameters"]
    def __init__(self):
        self.parameters = []
    def addParameters(self,parameters):
        self.parameters += parameters
    def copy(self,*args,**kwargs):
        a = type(self)(*args,**kwargs)
        a.parameters = [copy(p) for p in self.parameters]
        return a
    def resolveNames(self,symbolsTable,operator):
        for param in self.parameters:
            getattr(param,operator)(symbolsTable)
    def resolveLocal(self,symbolsTable):
        self.resolveNames(symbolsTable,"resolveLocal")
    def resolveCaller(self,symbolsTable):
        self.resolveNames(symbolsTable,"resolveCaller")
    def resolveTerminal(self,symbolsTable):
        self.resolveNames(symbolsTable,"resolveTerminal")    
    def legalIndex(self,actionMap,id):
        if not any((mapping.checkIndex(id) for mapping in actionMap)):
            self.errorHandler.illegalActionIndex(id)
    def resolveProperties(self,storage):
        if not hasattr(self,"raw_id"):
            self.errorHandler.unresolvedIdentifier()
        else:
            storage("actionID",self.raw_id)
            for ix,param in enumerate(self.parameters):
                if ix >= 5:
                    param.errorHandler.actionParameterCountExceeded(ix)
                    continue
                if hasattr(param,"raw_id"):
                    storage("actionUnkn%d"%ix,param.rawID)
                else:
                    param.errorHandler.unresolvedIdentifier()
class ActionLiteral(Action):
    def __init__(self,id):
        tag = "Action Literal [%d]"%id
        self.raw_id = id
        super().__init__()
    def substituteScope(self,*arg,**kwargs):
        pass
    def copy(self):
        return super().copy(copy(self.raw_id))
    def resolveAction(self,actionMap):
        self.legalIndex(actionMap,self.raw_id)
class ActionID(Action): 
    subfields = ["parameters","id"]
    def __init__(self,name):
        self.tag = "Action ID [%s]"%name
        self.id = name
        super().__init__()
    def substituteScope(self,*arg,**kwargs):
        pass
    def copy(self):
        return super().copy(copy(self.id))
    def resolveAction(self,actionMap):
        if not hasattr(self.id, "raw_id"):
            self.errorHandler.unresolvedIdentifier(self.id)
            return
        self.raw_id = self.id.raw_id
        self.legalIndex(actionMap,self.raw_id)
class ScopedAction(Action): 
    subfields = ["parameters","id"]
    def __init__(self,id):
        self.tag = "Action Scoped ID [%s]"%id
        self.id = id
        super().__init__()
    def substituteScope(self,moduleScope,actionScope):
        pass
    def copy(self):
        return super().copy(copy(self.scope),copy(self.id))
    def resolveAction(self,symbolsTable):
        try:
            self.raw_id = self.id.resolveAction(symbolsTable)
        except:
            self.errorHandler.missingActionScope(self.scope)
        #if self.scope not in actionMap:
        #    self.errorHandler.missingActionScope(self.scope)
        #    return
        #scope = actionMap[self.scope]
        #self.raw_id = scope.resolveAction(self.id)