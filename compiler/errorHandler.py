# -*- coding: utf-8 -*-
"""
Created on Mon Nov  8 21:50:22 2021

@author: Asterisk
"""
from collections.abc import Iterable
from collections import defaultdict

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
        return {copy(key): copy(val) for key, val in self.items()}
    else:
        return self.copy().copyMetadataFrom(self)


class ErrorManaged():
    subfields = []
    tag = None

    def inherit(self, settings=None, errorHandler=None):
        self.settings = self.settings if hasattr(
            self, "settings") else settings
        self.errorHandler = self.errorHandler if hasattr(
            self, "errorHandler") else errorHandler
        for subfield in self.subfields:
            self.inheritChildren(getattr(self, subfield))
        return self

    def inheritChildren(self, child):
        if type(child) in [str, int, float, type(None), bool]:
            pass
        elif isinstance(child, dict):
            for item in child.values():
                self.inheritChildren(item)
        elif isinstance(child, Iterable):
            for item in child:
                self.inheritChildren(item)
        else:
            child.inherit(
                self.settings, self.errorHandler.childInstance(self.tag))
        return child

    def copyMetadataFrom(self, original):
        self.settings = original.settings
        self.errorHandler = original.errorHandler
        return self

    def __repr__(self):
        return str(self)

    def __str__(self):
        return self.tag


class CompilationError():
    pass


class ErrorHandler():
    def __init__(self, settings):
        self.settings = settings
        self.mark = False
        self.trace = []
        self.log
        self.errorlog = []
        self.tags = []
        self.parent = None

    def childInstance(self, tag=None):
        eh = ErrorHandler(self.settings)
        if tag is not None:
            eh.tags.append(tag)
        eh.parent = self
        return eh

    def proceed(self):
        return not self.mark

    def log(self, level, string, tags=[]):
        if self.parent:
            self.parent.log(string, self.tags + tags)
        else:
            self.errorlog.append((level,tags,string,))
            if level == "CriticalError":
                self.report()
                raise CompilationError()
            if level == "Error":
                self.mark = True

    def report(self):
        perLevel = defaultdict(list)
        for level,tags,entry in sorted(self.errorlog):
            perLevel[level].append((tags,entry))
        for level in perLevel:
            self.settings.display("="*40)
            self.settings.display(level)
            for tags,entry in perLevel[level]:
                self.settings.display("  "+">".join(tags))
                self.settings.display("  "+entry)
                self.settings.display("-"*30)
        self.settings.display("="*40)

    def errorLevel(self):
        return "Error" if not self.settings.forceCritical else "CriticalError"

    def warningLevel(self):
        return "Warning" if not self.settings.forceError else self.errorLevel()

    def compiledModule(self, scope, path):
        level = "CriticalError"
        self.log(level, "Compiling with Pre-Compiled Modules is not supported yet")

    def registryCountExceeded(self, excess):
        level = self.errorLevel()
        self.log(
            level, "Registry Count Exceeded - Too Many Different Registers Used [%d]" % excess)

    def unresolvedIdentifier(self, identifier=""):
        level = self.errorLevel()
        self.log(level, "Unresolved Identifier %s" % str(identifier))

    def actionParameterCountExceeded(self, count):
        level = self.errorLevel()
        self.log(level, "Too many parameters passed to an action [%d/5]")

    def missingActionScope(self, scope):
        level = self.errorLevel()
        self.log(level, "Action Scope %s is not an import" % str(scope))

    def missingNodeName(self, name):
        level = self.errorLevel()
        self.log(
            level, "Call to %s cannot be resolved as no node has this name" % name)

    def missingScope(self, scope):
        level = self.errorLevel()
        self.log(level, "Scope %s is not an import" % str(scope))

    def thkIndexLimitExceeded(self, index):
        level = self.errorLevel()
        self.log(
            level, "Fand file specifies a smaller thk count than the one given [%d]" % index)

    def invalidMonsterName(self, target):
        level = self.errorLevel()
        self.log(level, "%s is not a valid monster name" % str(target))

    def invalidActionFile(self, path):
        level = self.errorLevel()
        self.log(level, "%s is not a valid monster action dump" % str(path))

    def missingActionName(self, name):
        level = self.errorLevel()
        self.log(level, "%s is not a valid monster name" % str(name))

    def missingAnyActionScope(self):
        level = self.errorLevel()
        self.log(
            level, "No valid monster found within project or file to resolve actions")

    def repeatedProperty(self, propertyName):
        level = self.settings.repeatedProperty
        self.log(level, "Property %s is specified multiple times in the same segment at compile time" % str(
            propertyName))

    def segmentDuplicateProperty(self):
        level = self.settings.repeatedProperty
        self.log(
            level, "Property is specified multiple times in the same segment at parse time")

    def resolutionError(self, propName):
        level = self.errorLevel()
        self.log(
            level, "Property %s could not be fully resolved during compilation" % propName)

    def missingCallTarget(self):
        level = self.errorLevel()
        self.log(
            level, "Call is lacking a proper target (normally from inlining failure)")

    def repeatedId(self):
        level = self.warningLevel()
        self.log(
            level, "Node is trying to use already taken ID and will overwrite previous instance")
    
    def repeatedIndex(self):
        level = self.warningLevel()
        self.log(
            level, "Node is trying to use pre-existing index and will overwrite previous instance")
    
    def repeatedName(self):
        level = self.warningLevel()
        self.log(
            level, "Node name already exists and will overwrite previous instance.")
    