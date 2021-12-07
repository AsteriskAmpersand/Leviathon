# -*- coding: utf-8 -*-
"""
Created on Tue Dec  7 06:19:30 2021

@author: Asterisk
"""
from decompiler.decompilerUtils import Decompiler, ENC_NODE
from decompiler.segmentDecompiler import SegmentDecompiler
from common import keywords as key


class NodeDecompiler(Decompiler):
    def __init__(self, index=None, settings=None):
        super().__init__(settings)
        self.names = []
        self.index = index
        self.indexOverride = False
        self.idOverride = False

    def read(self, node):
        self.node = node
        self.id = node.id
        self.index = node.index if hasattr(node, "index") else self.index
        self.segments = [SegmentDecompiler(self.settings).read(
            segment) for segment in self.node.segments]
        return self

    def label(self, index, name=""):
        if name:
            self.names.append(name)
        else:
            self.names.append("node_%03d" % index)

    def explicitPosition(self, val):
        self.indexOverride = val

    def explicitId(self, val):
        self.idOverride = val

    def getName(self):
        return self.names[0]

    def headerText(self, position=False, showId=True):
        header = key.DEF + " "
        header += " & ".join(self.names)
        if showId and self.idOverride:
            header += " : " + str(self.id)
        if position or self.indexOverride:
            header += " @ %d" % self.index
        header += "\n"
        return header

    def malformedTHK(self, indentationDepth, segmentString):
        if self.settings.suppressWarnings:
            return ""
        placeholder = "*& " if self.settings.genPlaceholder else ""
        return '\t'*indentationDepth+placeholder +\
            "// -Illegal Context was commented out '" +\
            segmentString.replace("\n", "") + "'\n"

    def decompile(self, *args, position=False, **kwargs):
        missingLocalReferences = []
        result = ""
        result += self.headerText(position)
        indentationDepth = 1
        enclosure = [ENC_NODE]
        for segment in self.segments:
            segmentString = segment.decompile(*args, **kwargs)
            contextStart = segment.contextStart()
            if contextStart:
                enclosure.append(contextStart)
            contextEnd = segment.contextEnd()
            if contextEnd:
                if (not enclosure or contextEnd != enclosure[-1]):
                    result += self.malformedTHK(indentationDepth,
                                                segmentString)
                    continue
                else:
                    enclosure.pop()
            contextDependent = segment.contextMid()
            if contextDependent:
                if not enclosure or contextDependent != enclosure[-1]:
                    result += self.malformedTHK(indentationDepth,
                                                segmentString)
                    continue
            indentationDepth -= segment.checkSubstraction()
            result += '\t'*indentationDepth + segmentString
            indentationDepth += segment.checkAddition()
            missingLocalReferences += segment.missingLocalReferences
        self.missingLocalReferences = missingLocalReferences
        while(enclosure):
            item = enclosure.pop()
            indentationDepth -= 1
            result += '\t'*indentationDepth + item
            if not self.settings.suppressWarnings:
                result += " // -Added by the Decompiler to ammend syntactically malformed thk\n"
        return result+"\n"
