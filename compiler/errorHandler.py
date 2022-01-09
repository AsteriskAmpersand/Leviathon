# -*- coding: utf-8 -*-
"""
Created on Mon Nov  8 21:50:22 2021

@author: Asterisk
"""
from collections.abc import Iterable
from collections import defaultdict, deque
from compiler.compilerErrors import CompilationError


def iterable(obj):
    try:
        iter(obj)
    except:
        return False
    return True


def copy(self):
    # if hasattr(self,"copy"):
    #    return self.copy().copyMetadataFrom(self)
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
    elif type(self) is list:
        return [copy(obj) for obj in self]
    elif type(self) is deque:
        return deque([copy(obj) for obj in self])
    else:
        return self.copy().copyMetadataFrom(self)


class ErrorManaged():
    subfields = []
    tag = None

    def inherit(self, settings=None, errorHandler=None):
        self.settings = self.settings if settings is None else settings
        self.errorHandler = self.errorHandler \
            if errorHandler is None \
            else errorHandler
        for subfield in self.subfields:
            self.inheritChildren(getattr(self, subfield))
        return self

    def verifyElement(self, element):
        if not hasattr(element, "verify"):
            # if not issubclass(type(element),ErrorManaged):
            return
        failed = False
        try:
            if element.errorHandler.parent.fullTags() != self.errorHandler.fullTags():
                self.settings.display(
                    "Missing Inheritance <", self.tag, "> <= <", element.tag, ">")
                self.settings.display(repr(self))
                self.settings.display(repr(element))
                failed = True
        except:
            self.settings.display(
                "Missing Error Handler [", self.tag, "] -> ", element.tag)
            self.settings.display(repr(self))
            self.settings.display(repr(element))
            failed = True
        if failed:

            raise AttributeError
        if self.errorHandler.mark:
            self.errorHandler.report()
            raise CompilationError()
        element.verify()

    def verify(self):
        for subfield in self.subfields:
            var = getattr(self, subfield)
            if type(var) is dict:
                for key, value in var.items():
                    self.verifyElement(key)
                    self.verifyElement(value)
            elif iterable(var):
                for element in var:
                    self.verifyElement(element)
            else:
                self.verifyElement(var)

    def inheritChildren(self, child):
        if issubclass(type(child), ErrorManaged):
            child.inherit(
                self.settings, self.errorHandler.childInstance(self.tag))
        elif type(child) in [str, int, float, type(None), bool]:
            pass
        elif isinstance(child, dict):
            for item in child.values():
                self.inheritChildren(item)
            for key in child.keys():
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


def unique(seq):
    seen = set()
    seen_add = seen.add
    return [(x, y) for x, y in seq if not ((tuple(x), y) in seen or seen_add((tuple(x), y)))]


class ErrorHandler():
    def __init__(self, settings):
        self.settings = settings
        self.mark = False
        self.trace = []
        self.log
        self.errorlog = []
        self.tags = []
        self.parent = None

    def fullTags(self):
        return self.tags + self.parent.fullTags() if self.parent else []

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
            self.parent.log(level, string, self.tags + tags)
        else:
            self.errorlog.append((level, tags, string,))
            if level == "CriticalError":
                self.report()
                self.mark = True
                raise CompilationError()
            if level == "Error":
                self.mark = True

    def report(self):
        perLevel = defaultdict(list)
        for level, tags, entry in sorted(self.errorlog):
            perLevel[level].append((tags, entry))
        for level in perLevel:
            self.settings.display("="*40)
            self.settings.display(level)
            for tags, entry in unique(perLevel[level]):
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

    def unresolvedScopeInRegister(self, identifier=""):
        level = self.errorLevel()
        self.log(level, "Unresolved Scoped Identifier in Register %s" %
                 str(identifier))

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

    def missingExternalNodeName(self, scope, name):
        level = self.errorLevel()
        self.log(
            level, "Call to %s cannot be resolved as no node has this name in module %s" % (name, scope))

    def missingScope(self, scope):
        level = self.errorLevel()
        self.log(level, "Scope %s is not an import" % str(scope))

    def missingScopeNode(self, scope, node):
        level = self.errorLevel()
        self.log(level, "Node %s is missing from Scope %s" %
                 (str(node), str(scope)))

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

    def missingActionName(self, actionName, monsterName):
        level = self.errorLevel()
        self.log(level, "%s is not a valid action name for monster %s" %
                 (str(actionName), str(monsterName)))

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

    def unmatchedFunctionSignature(self, signature):
        level = self.errorLevel()
        self.log(
            level, "No Function Signature in the FEXTY File matches the one provided '%s'" % signature)

    def repeatedId(self):
        level = self.warningLevel()
        self.log(
            level, "Node is trying to use already taken ID and will overwrite previous instance")

    def repeatedIndex(self):
        level = self.warningLevel()
        self.log(
            level, "Node is trying to use pre-existing index and will overwrite previous instance")

    def repeatedName(self, name):
        level = self.warningLevel()
        self.log(
            level, "Node name %s already exists and will overwrite previous instance." % name)

    def lexingFail(self, path=""):
        level = self.errorLevel()
        self.log(
            level, "Failed to Parse File %s." % path)
