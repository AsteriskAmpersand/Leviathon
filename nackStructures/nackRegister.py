# -*- coding: utf-8 -*-
"""
Created on Thu Nov 25 04:42:16 2021

@author: Asterisk
"""
from errorHandler import ErrorManaged,copy

class Register():
    def resolveLocal(self,symbolsTable):
        pass
    def resolveCaller(self,symbolsTable):
        pass
    def resolveTerminal(self,symbolsTable):
        pass
    def resolveName(self,namespace):
        if hasattr(self,"raw_id"):
            return
        if self.identifier not in namespace:
            self.errorHandler.missingRegisterName(self.identifier)
        else:
            self.raw_id = namespace[self.identifier]
    def collectRegisters(self):
        if hasattr(self,"raw_id"):
            return [self.raw_id]
        else:
            return [str(self.identifier)]
class RegisterID(Register,ErrorManaged):
    tag = "Register ID"
    subfields = ["identifier"]
    def __init__(self,id):
        self.tag = "Register ID [%s]"%(id)
        self.identifier = id
    def copy(self):
        return RegisterID(copy(self.identifier))
class RegisterLiteral(Register,ErrorManaged):
    tag = "Register Literal"
    subfields = ["identifier"]
    def __init__(self,id):
        self.tag = "Register ID [%s]"%(id)
        self.identifier = id
        self.raw_id = id
    def copy(self):
        return RegisterID(copy(self.identifier))
class RegisterOp():
    typing = "register"
    def resolveImmediateId(self,varNames):
        pass
    def resolveCallerId(self,varNames):
        pass
    def resolveTerminalId(self,varNames):
        pass
    def resolveName(self,namespace):
        self.base.resolveName(namespace)    
    def collectRegisters(self):
        return self.base.collectRegisters()
    
regSymbols = ["==","<=" ,"<" ,">=" ,">" ,"!="]
regComps = {regSymbols[i]:i for i in range(len(regSymbols))}
class RegisterComparison(RegisterOp,ErrorManaged):
    subfields = ["base","target","comparison"]
    def __init__(self,ref,val,comp):
        self.tag = "Register Comparison [%s %s %s]"%(ref,comp,val)
        self.base = ref
        self.target = val
        self.comparison = comp
    def copy(self):
        return RegisterComparison(copy(self.base),
                                  copy(self.target),
                                  copy(self.comparison))
    def resolveNames(self,symbolsTable,operator):
        getattr(self.target,operator)(symbolsTable)
    def resolveLocal(self,symbolsTable):
        self.resolveNames(symbolsTable,"resolveLocal")
    def resolveCaller(self,symbolsTable):
        self.resolveNames(symbolsTable,"resolveCaller")
    def resolveTerminal(self,symbolsTable):
        self.resolveNames(symbolsTable,"resolveTerminal")
    def resolveProperties(self,storage):
        if not hasattr(self.base,"raw_id"):
            self.errorHandler.unresolvedIdentifier(str(self.base))
        elif not hasattr(self.target,"raw_id"):
            self.errorHandler.unresolvedIdentifier(str(self.target))
        else:
            storage("functionType",0x94+self.base.raw_id)
            storage("parameter1",regComps[self.comparison])
            storage("parameter2",self.target.raw_id)
unaryOps = {"++":0,"|-":1}
class RegisterUnaryOp(RegisterOp,ErrorManaged):
    tag = "Register Unary Operator"
    subfields = ["base","operator"]
    def __init__(self,ref,op):
        self.base = ref
        self.operator = op
    def copy(self):
        return RegisterUnaryOp(copy(self.base),copy(self.operator))
    def resolveProperties(self,storage):
        if not hasattr(self.base,"raw_id"):
            self.errorHandler.unresolvedIdentifier(str(self.base))
        else:
            storage("functionType",0x94+self.base.raw_id)
            storage("parameter1",unaryOps[self.operator])