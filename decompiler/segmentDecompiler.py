# -*- coding: utf-8 -*-
"""
Created on Tue Dec  7 06:21:42 2021

@author: Asterisk
"""

from decompiler.decompilerUtils import Decompiler, ENC_NODE, ENC_COND, ENC_RNG
from decompiler.thkDecompileUtils import MissingCallID, CallResolver
from common.registerOperations import getRegisterIndex, isRegister
from common.thk import Segment
from common import keywords as key


def spaceIfOp(string):
    if not string:
        return string
    return string + " "


class SegmentDecompiler(Decompiler):
    def __init__(self, settings=None):
        super().__init__(settings)
        self.initMembers()

    def initMembers(self):
        self.addIndent = False
        self.removeIndent = False
        self.encloseStart = None
        self.encloseEnd = None
        self.encloseMid = None

        self.used = set()
        self.missingLocalReferences = []
        self.active = False
        self.flow = ""
        self.function = ""
        self.action = ""
        self.call = ""
        self.directive = ""
        self.meta = ""

        self.functionName = ""
        self.actionName = ""
        self.callName = ""
        self.comments = ""
        self.registers = []

    def read(self, segment):
        self.segment = segment
        segment.log = self.log
        if isRegister(self.segment): #0x80 <= self.segment.functionType <= 0xab:
            self.registers.append(getRegisterIndex(self.segment))
        return self

    def getActionParams(self, segment):
        i = 4
        def field(i): return "actionUnkn%d" % i
        def getField(i): return getattr(segment, field(i))
        while (i >= 0 and getField(i) == 0):
            i -= 1
        params = [str(getField(j))
                  for j in range(i+1) if segment.log(field(j)) or True]
        return ','.join(params)

    def resolveActions(self, actionResolver):
        if self.segment.actionID != 0:
            self.log("actionID")
            self.actionName = actionResolver.resolveActionIndex(
                self.segment.actionID)
            self.actionParams = self.getActionParams(self.segment)
            self.action = key.DO_ACTION + " " + \
                self.actionName + "(" + self.actionParams + ")"
        else:
            return None

    def resolveCalls(self, callResolver, scopeResolver):
        try:
            scope, callName = callResolver.resolve(self.segment)
        except MissingCallID as m:
            if m.scopeIndex == "local":
                self.missingLocalReferences.append((m.scopeIndex, m.id))
            else:
                if self.settings.raiseInvalidReference:
                    raise
                if not self.settings.suppressWarnings:
                    self.comments += "-THK_%02d is missing NodeID %03d. " % (
                        m.scopeIndex, m.id)
            scope = m.scopeIndex
            callName = CallResolver.defaultCall(m.id)
        if scope == "local":
            self.callName = callName
            self.call = key.DO_CALL+" %s" % callName
        elif scope is not None:
            self.callName = callName
            self.call = key.DO_CALL + \
                " %s.%s" % (scopeResolver.resolve(scope), callName)

    def resolveFunctions(self, functionResolver, registerScheduler):
        if self.segment.functionType not in [0, 2]:
            invert = False
            if self.segment.functionType < 0:
                invert = True
                self.segment.functionType = - self.segment.functionType
            if isRegister(self.segment):
                self.functionName = functionResolver.registerResolve(
                    self.segment, registerScheduler)
            else:
                self.functionName = functionResolver.resolve(self.segment)
            self.functionName = ("not " if invert else "") + self.functionName
            self.function = self.functionName
            return self.functionName
        return None

    def decompile(self, actionResolver, callResolver, scopeResolver, functionResolver, registerScheduler):
        self.checkActive()
        self.checkFlow()
        self.resolveActions(actionResolver)
        self.resolveCalls(callResolver, scopeResolver)
        self.resolveFunctions(functionResolver, registerScheduler)
        self.checkDirective()
        self.checkMeta()
        if not any([self.flow, self.function, self.action, self.call]):
            if self.directive:
                self.directive = self.directive[3:]
        code = ''.join(map(spaceIfOp, [
                       self.flow, self.function, self.action, self.call, self.directive, self.meta]))
        if code == "":
            code = "*&"
        if self.comments:
            code += "// " + self.comments
        return code + "\n"

    def checkActive(self):
        segment = self.segment
        # action call directive
        self.active |= segment.functionType > 2
        self.active |= segment.extRefThkID != -1 or segment.localRefNodeID != -1
        self.active |= segment.actionID != 0

    def checkFlow(self):
        self.checkConditional()
        self.checkTerminal()
        self.checkChance()
        self.checkEndNode()

    def checkEndNode(self):
        segment = self.segment
        if segment.endRandom == 1:
            self.flow = key.ENDF
            self.removeIndent = True
            self.encloseEnd = ENC_NODE
            self.log("nodeEndingData")
            self.log("endRandom")
            return True
        return False

    def checkChance(self):
        chanceIndent = 3
        segment = self.segment
        if segment.branchingControl == 0x1:
            if self.active:
                self.flow = key.ENDRW
                self.removeIndent = chanceIndent
                self.encloseEnd = ENC_RNG
                self.log("branchingControl")
            else:
                self.flow = key.ENDR
                self.removeIndent = chanceIndent
                self.encloseEnd = ENC_RNG
                self.log("branchingControl")
            return True
        if segment.endRandom in [0x40, 0xC0, 0x80]:
            if segment.endRandom == 0x40:
                self.flow = key.RANDOM+" (%d)" % segment.parameter1
                self.addIndent = chanceIndent
                self.encloseStart = ENC_RNG
            else:
                # 0xC0 Chance, 0x80 Last Chance
                self.removeIndent = chanceIndent
                self.addIndent = chanceIndent
                self.encloseMid = ENC_RNG
                self.flow = key.ELSER+" (%d)" % segment.parameter1
            self.log("endRandom").log("parameter1")
            return True
        return False

    def checkConditional(self):
        segment = self.segment
        if segment.branchingControl == 0x2:
            self.flow = key.IF
            self.addIndent = True
            self.encloseStart = ENC_COND
        elif segment.branchingControl == 0x4:
            if segment.functionType > 2:
                self.flow = key.ELIF
                self.encloseMid = ENC_COND
                self.removeIndent = True
                self.addIndent = True
            else:
                self.flow = key.ELSE
                self.removeIndent = True
                self.addIndent = True
                self.encloseMid = ENC_COND
        elif segment.branchingControl == 0x8:
            if self.active:
                self.flow = key.ENDIFW
                self.removeIndent = True
                self.encloseEnd = ENC_COND
            else:
                self.flow = key.ENDIF
                self.removeIndent = True
                self.encloseEnd = ENC_COND
        else:
            return False
        self.log("branchingControl")
        return True

    def checkTerminal(self):
        segment = self.segment
        if segment.branchingControl == 0x10:
            self.flow = key.ENDALL
            self.log("branchingControl")
            return True
        return False

    def checkDirective(self):
        segment = self.segment
        if segment.flowControl == 0x4:
            self.directive = key.DO_DIRECTIVE + " " + key.REPEAT
        elif segment.flowControl == 0x8:
            self.directive = key.DO_DIRECTIVE + " " + key.RETURN
        elif segment.flowControl == 0x80:
            self.directive = key.DO_DIRECTIVE + " " + key.RESET
        else:
            return False
        self.log("flowControl")
        return True

    def checkMeta(self):
        segment = self.segment
        meta = {}
        self.used.add("monsterID")
        self.used.add("isPalico")
        self.used.add("padding")
        for value in Segment.subcons:
            if value.name not in self.used:
                var = getattr(segment, value.name)
                if var != 0:
                    if value.name == "functionType" and var == 2:
                        pass
                    elif value.name in ['extRefThkID', 'extRefNodeID', 'localRefNodeID']\
                            and var == -1:
                        pass
                    else:
                        meta[value.name] = var
        if meta:
            self.meta = key.META + " " + \
                ", ".join((key+":"+str(val) for key, val in meta.items()))

    def checkAddition(self):
        return self.addIndent

    def checkSubstraction(self):
        return self.removeIndent

    def contextStart(self):
        return self.encloseStart

    def contextEnd(self):
        return self.encloseEnd

    def contextMid(self):
        return self.encloseMid

    def log(self, varname):
        if varname in self.used:
            raise ValueError(
                "Segment is using the same field (%s) more than once" % varname)
        self.used.add(varname)
        return self