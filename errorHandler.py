# -*- coding: utf-8 -*-
"""
Created on Mon Nov  8 21:50:22 2021

@author: Asterisk
"""
from collections.abc import Iterable

def copy(self):
    if type(self) is int:
        return self
    elif type(self) is str:
        return self
    elif type(self) is type(None):
        return self
    elif type(self) is bool:
        return self
    elif type(self) is dict:
        return {copy(key):copy(val) for key,val in self.items()}
    else:
        return self.copy().copyMetadataFrom(self)

class ErrorManaged():
    subfields = []
    tag = None
    def inherit(self,settings=None,errorHandler=None):
        self.settings = self.settings if hasattr(self,"settings") else settings
        self.errorHandler = self.errorHandler if hasattr(self,"errorHandler") else errorHandler
        for subfield in self.subfields:
            self.inheritChildren(getattr(self,subfield))
        return self
    def inheritChildren(self,child):
        if type(child) in [str,int,float,type(None),bool]:
            pass
        elif isinstance(child,dict):
            for item in child.values():
                self.inheritChildren(item)
        elif isinstance(child, Iterable):
            for item in child:
                self.inheritChildren(item)
        else:
            child.inherit(self.settings,self.errorHandler.childInstance(self.tag))
        return child
    def copyMetadataFrom(self,original):
        self.settings = original.settings
        self.errorHandler = original.errorHandler
        return self
    def __repr__(self):
        return str(self)
    def __str__(self):
        return self.tag

class ErrorHandler():
    def __init__(self,settings):
        self.settings = settings
        self.mark = False
        self.trace = []
        self.errorlog = []
        self.tags = []
        self.parent = None
    def childInstance(self,tag = None):
        eh = ErrorHandler(self.settings)
        if tag is not None: eh.tags.append(tag)
        eh.parent = self
        return eh
    def proceed(self):
        return not self.mark
    def log(self,string,tags = []):
        if self.parent:
            self.parent.log(string,self.tags + tags)
        else:
            self.log.append((string,tags))
    def report(self):
        for entry in self.errorlog:
            print(entry)