# -*- coding: utf-8 -*-
"""
Created on Mon Oct 11 02:22:25 2021

@author: Asterisk
"""
from sly import Parser
from sly.lex import Token
import collections as col
import logging
import itertools

from nackLex import NackLexer

class SemanticError(Exception):
    pass

class NackFile():
    def __init__(self):
        self.scopeNames = {}
        self.actionScopeNames = {}
    def addNodes(self,nodeList):
        self.nodes = nodeList
class ScopeTarget():
    def __init__(self,target,type):
        self.target = target
        self.type = type
class ActionTarget():
    def __init__(self,target,typing):
        self.target = target
        self.typing = typing
class Identifier():
    def __init__(self,identifier):
        self.id = identifier
    def __str__(self):
        return str(self.id)
class IdentifierRaw():
    def __init__(self,identifier):
        self.raw_id = identifier
class Node():
    def __init__(self,header,bodylist):
        self.header = header
        self.bodylist = bodylist
class NodeHeader():
    def __init__(self,aliaslist,index):
        self.names = aliaslist
        self.index = index
class Segment():
    def __init__(self):
        self._function = None
        self._call = None
        self._directive = None
        self._flowControl = None
        self._endRandomType = None
        self._terminator = None
    def existingCheck(self,check):
        if getattr(self,"_"+check) is not None:
            raise SemanticError("Segment already has been assigned a %s"%check)
    def addFunction(self,function):
        self.existingCheck("function")
        self._function = function
    def addCall(self,call):
        self.existingCheck("call")
        self._call = call
    def addDirective(self,directive):
        self.existingCheck("directive")
        self._directive = directive
    def startConditional(self):
        self.existingCheck("flowControl")
        self._flowControl = "ConditionalStart"
    def addConditionalBranch(self):
        self.existingCheck("flowControl")
        self._flowControl = "ConditionalBranch"
    def endConditional(self):
        self.existingCheck("flowControl")
        self._flowControl = "ConditionalEnd"
    def addEnd(self):
        self.existingCheck("terminator")
        self._terminator = True
    def addChance(self,chance):
        self.existingCheck("endRandomType")
        self._endRandomType = "Chance"
    def endChance(self):
        self.existingCheck("flowControl")
        self._flowControl = "ChanceEnd"
class Chance():
    def __init__(self,percentage):
        self.chance = percentage
class ChanceHead(Chance):
    pass
class ChanceElse(Chance):
    pass
class FunctionShell():
    def __init__(self,string):
        self.content = string
class Register():
    pass
class RegisterID(Register):
    def __init__(self,id):
        self.identifier = id
class RegisterComparison(Register):
    def __init__(self,ref,val,comp):
        self.base = ref
        self.target = val
        self.comparison = comp
class RegisterUnaryOp(Register):
    def __init__(self,ref,op):
        self.base = ref
        self.operator = op
class Call():
    pass
class CallID(Call):
    def __init__(self,hardId):
        self.raw_target = hardId
class ScopedCall(Call):
    def __init__(self,scope,target):
        self.scope = scope
        self.target = target
class Directive():
    def __init__(self,command):
        self.raw_target = {"return":0x8,"repeat":0x4,"reset":0x80}[command]

class NackParser(Parser):
    log = logging.getLogger()
    #log.setLevel(logging.ERROR)
    # Get the token list from the lexer (required)
    tokens = NackLexer.tokens
    debugfile = 'nackParser.out'

    def parse(self,iterableTokens):
        self.file = NackFile()
        t = Token()
        t.type = "LINESKIP"
        t.value = '\n'
        t.lineno = -1
        t.index = -1
        return super().parse(itertools.chain(iterableTokens,[t]))

    #===================================================
    # File
    #===================================================

    @_('nackHeader nackBody')
    def nackFile(self,p):
        #header handed through individual methods
        self.file.addNodes(p.nackBody)
        return self.file
    
    @_('empty')
    def nackHeader(self,p):
        pass #handled implicitly
    @_('libraryImport nackHeader')
    def nackHeader(self,p):
        pass #handled by library import code
    @_('actionImport nackHeader')
    def nackHeader(self,p):
        return  #handled by action import code
    @_('registerDeclaration nackHeader')
    def nackHeader(self,p):
        pass #handled by register declaration code
    
    @_('IMPORTLIBRARY PATH AS ID skip')
    def libraryImport(self,p):
        self.file.scopeNames[p.ID] = ScopeTarget(p.PATH,"path")
    @_('IMPORTLIBRARY ID AS ID skip')
    def libraryImport(self,p):
        self.file.scopeNames[p.ID0] = ScopeTarget(p.ID1,"id")
    @_('IMPORTLIBRARY numeric AS ID skip')
    def libraryImport(self,p):
        self.file.scopeNames[p.numeric] = ScopeTarget(p.ID,"id")
    
    @_('IMPORTACTIONS PATH AS ID skip')
    def actionImport(self,p):
        self.file.actionScopeNames[p[3]] = ActionTarget(p[1],"id")
    @_('IMPORTACTIONS ID AS ID skip')
    def actionImport(self,p):
        self.file.actionScopeNames[p[3]] = ActionTarget(p[1],"path")
    @_('REGISTER id skip')
    def registerDeclaration(self,p):
        self.file.registerNames[p.id] = None
    @_('REGISTER id AS REG skip')
    def registerDeclaration(self,p):
        self.file.registerNames[p.id] = ord(p.REG[1])-ord('A')
    
    @_('node nackBody')
    def nackBody(self,p):
        p.nackBody.appendleft(p.node)
        return p.nackBody
    @_('empty')
    def nackBody(self,p):
        return col.deque()

    #===================================================
    # Node
    #===================================================
    
    @_('defHeader nodeBody nodeEnd')
    def node(self,p):
        return Node(p.defHeader,p.nodeBody+p.nodeEnd)
    
    @_('DEF id nodeAlias nodeIndex skip')
    def defHeader(self,p):
        p.nodeAlias.appendleft(p.id)
        return NodeHeader(p.nodeAlias,p.nodeIndex)
    
    @_('"&" id nodeAlias')
    def nodeAlias(self,p):
        p.nodeAlias.appendleft(p.id)
        return p.nodeAlias
    @_('empty')
    def nodeAlias(self,p):
        return col.deque()

    @_('":" numeric')
    def nodeIndex(self,p):
        return p.numeric,None
    @_('":" numeric META numeric')
    def nodeIndex(self,p):
        return p.numeric0,p.numeric1
    @_('META numeric')
    def nodeIndex(self,p):
        return None,p.numeric
    @_('empty')
    def nodeIndex(self,p):
        return None,None
    
    @_('segment nodeBody')
    def nodeBody(self,p):
        return p.segment + p.nodeBody
    @_('empty')
    def nodeBody(self,p):
        return col.deque()
    
    @_('ENDF maybeMetaType skip',
       'ENDDEF maybeMetaType skip',
       'ENDFUNCTION maybeMetaType skip')
    def nodeEnd(self,p):
        s = p.maybeMetaType
        s.addEnd()
        return col.deque([s])

    #===================================================
    # Segment
    #===================================================
    @_('chance')
    def segment(self,p):
        return p.chance
    @_('conditional')
    def segment(self,p):
        return p.conditional
    @_('CONCLUDE uncontrolledSegment')
    def segment(self,p):
        p.uncontrolledSegment.addConclude()
        return col.deque([p])
    @_('uncontrolledSegment')
    def segment(self,p):
        return col.deque([p.uncontrolledSegment])
    @_('UNSAFE skip')
    def segment(self,p):
        return col.deque([UnsafeSegment(p.UNSAFE)])
    @_('DO_NOTHING skip')
    def segment(self,p):
        return col.deque([Segment()])

    #===================================================
    # Chance
    #===================================================
    
    @_('chanceHeader actionTypeStart nodeBody chanceBody uncontrolledSegment nodeBody optionalChance')
    def chance(self,p):
        p.actionTypeStart.addChance(p.chanceHeader)
        p.nodeBody0.appendleft(p.actionTypeStart)
        p.uncontrolledSegment.addChance(p.chanceBody)
        p.nodeBody1.appendleft(p.uncontrolledSegment)
        return p.nodeBody0 + p.nodeBody1 + p.optionalChance
    
    @_('chanceBody actionTypeStart nodeBody optionalChance')
    def optionalChance(self,p):
        s = p.actionTypeStart
        s.addChance(p.chanceBody)
        p.nodeBody.appendleft(s)
        return p.nodeBody + p.optionalChance
    @_('optionalTerminator')
    def optionalChance(self,p):
        return col.deque([p.optionalTerminator])
    
    @_("ENDC skip",
       "ENDCHANCE skip")
    def optionalTerminator(self,p):
        s = Segment()
        s.endChance()
        return s
    @_("ENDCWITH uncontrolledSegment skip",
       "ENDCHANCEWITH uncontrolledSegment skip")
    def optionalTerminator(self,p):
        s = p.uncontrolledSegment
        s.endChance()
        return s
    
    @_('CHANCE "(" numeric ")"',
       'CHANCE "(" id ")"')
    def chanceHeader(self,p):
        return ChanceHead(p[1])
    
    @_('elsechance "(" numeric ")"',
       'elsechance "(" id ")"')
    def chanceBody(self,p):
        #print(p.numeric.raw_id)
        return ChanceElse(p[2])
    
    @_('ELSECHANCE','ELSEC')
    def elsechance(self,p):
        return
    
    #===================================================
    #===================================================
    # Conditionals
    #===================================================
    @_('IF uncontrolledSegment nodeBody conditionalTerminator')
    def conditional(self,p):
        s = p.uncontrolledSegment
        s.startConditional()
        p.nodeBody.appendleft(s)
        return p.nodeBody + p.conditionalTerminator
    
    @_('ELIF functionType actionTypeStart nodeBody conditionalTerminator')
    def conditionalTerminator(self,p):
        s = p.actionTypeStart
        s.addFunction(p.functionType)
        s.addConditionalBranch()
        p.nodeBody.appendleft(s)
        p.nodeBody.append(p.conditionalTerminator)
        p.nodeBody.append(p.conditionalTerminator)
        return p.nodeBody
    @_('ELSE actionTypeStart nodeBody conditionalTerminator')
    def conditionalTerminator(self,p):
        s = p.actionTypeStart
        s.addConditionalBranch()
        p.nodeBody.appendleft(s)
        p.nodeBody.append(p.conditionalTerminator)
        return p.nodeBody
    
    @_('ENDIF skip')
    def conditionalTerminator(self,p):
        s = Segment()
        s.endConditional()
        return s
    @_('ENDWITH uncontrolledSegment')
    def conditionalTerminator(self,p):
        p.uncontrolledSegment.endConditional()
        return p.uncontrolledSegment
    
    #===================================================
    #===================================================
    # Basic Segments
    #===================================================    
    @_('maybeFunctionType actionTypeStart')
    def uncontrolledSegment(self,p):
        if p.maybeFunctionType:
            p.actionTypeStart.addFunction(p.maybeFunctionType)
        return p.actionTypeStart
    @_('directiveName maybeMetaType skip')
    def uncontrolledSegment(self,p):
        p.maybeMetaType.addDirective(p.directiveName)
        return p.maybeMetaType
    @_('maybeActionType maybeCallType maybeDirectiveType maybeMetaType skip')
    def actionTypeStart(self,p):
        s = p.maybeMetaType
        if p.maybeActionType: s.addAction(p.maybeActionType)
        if p.maybeCallType: s.addCall(p.maybeCallType)
        if p.maybeDirectiveType: s.addDirective(p.maybeDirectiveType)
        return s
    
    @_('functionType')
    def maybeFunctionType(self,p):
        return p[0]
    @_('empty')
    def maybeFunctionType(self,p):
        return None
    
    @_('actionType')
    def maybeActionType(self,p):
        return p[0]
    @_('empty')
    def maybeActionType(self,p):
        return None
    
    @_('callType')
    def maybeCallType(self,p):
        return p[0]
    @_('empty')
    def maybeCallType(self,p):
        return None
    
    @_('directiveType')
    def maybeDirectiveType(self,p):
        return p[0]
    @_('empty')
    def maybeDirectiveType(self,p):
        return None
    
    @_('metaType')
    def maybeMetaType(self,p):
        return p[0]
    @_('empty')
    def maybeMetaType(self,p):
        return Segment()
    #===================================================
    #===================================================
    # Basic Types
    #===================================================
    # Function
    @_('functionName','functionLiteral','registerType')
    def functionType(self,p):
        return p[0]
    
    # Action
    @_('DO_ACTION actionName actionParens','DO_ACTION actionLiteral actionParens')
    def actionType(self,p):
        p[1].addParameters(p[2])
        return p[1]
    
    # Call
    @_('DO_CALL callName')
    def callType(self,p):
        return p.callName

    # Directive
    @_('DO_DIRECTIVE directiveName')
    def directiveType(self,p):
        return p.directiveName

    # Meta
    @_('META metaparams')
    def metaType(self,p):
        s = Segment()
        s.addMeta(p.metaparams)
        return s


    #===================
    # Function Types
    #===================
    @_('FUNCTION_START id')
    def functionName(self,p):
        return FunctionShell(str(p.id))
    @_('FUNCTION_START id parens')
    def functionName(self,p):
        return FunctionShell(str(p.id)+p.parens)
    @_('FUNCTION_START id maybeParens maybeSubFunction')
    def functionName(self,p):
        return FunctionShell(''.join((str(p[i]) for i in range(1,len(p)))))
    
    @_('"." id maybeParens')
    def maybeSubFunction(self,p):
        return ''.join(map(str,p))
    @_('"." id parens maybeSubFunction')
    def maybeSubFunction(self,p):
        return ''.join(p)
    
    @_('parens')
    def maybeParens(self,p):
        return p.parens
    @_('empty')
    def maybeParens(self,p):
        return ""
    
    @_('"(" ")"')
    def parens(self,p):
        return ''.join(p)
    @_('funcParens')
    def parens(self,p):
        if type(p.funcParens) is str:
            return "("+p.funcParens+")"
        else:
            return "("+','.join(map(str,p.funcParens))+")"
    
    @_('FUNCTION maybeFuncParens')
    def functionLiteral(self,p):
        if type(p.maybeFuncParens) is str:
            raise SemanticError("Function literals cannot take hollow literals")
        FunctionLiteral(p.FUNCTION,p.maybeFuncParens)
    
    @_('empty')
    def maybeFuncParens(self,p):
        return []
    @_('funcParens')
    def maybeFuncParens(self,p):
        return p.funcParens
    
    @_('empty')
    def maybeDotID(self,p):
        return ''
    @_('"." id maybeDotID')
    def maybeDotID(self,p):
        return ''.join(map(str,p))
    
    @_('"(" id "." id maybeDotID ")"')
    def funcParens(self,p):
        return ''.join((str(p[i]) for i in range(1,5)))
    @_('"(" numericSymbol commaPrefacedId ")"')
    def funcParens(self,p):
        p.commaPrefacedId.appendleft(p.numericSymbol)
        return p.commaPrefacedId
    
    @_('empty')
    def commaPrefacedId(self,p):
        return col.deque()
    @_('"," numericSymbol commaPrefacedId')
    def commaPrefacedId(self,p):
        p.commaPrefacedId.appendleft(p.numericSymbol)
        return p.commaPrefacedId

    #===================
    # Action Types
    #===================
    
    @_('"(" maybeActionParams ")"')
    def actionParens(self,p):
        return p.maybeActionParams
    
    @_('empty')
    def maybeActionParams(self,p):
        return col.deque()
    @_('numeric maybeMoreActionParams')
    def maybeActionParams(self,p):
        p.maybeMoreActionParams.appendleft(numeric)
        return p.maybeMoreActionParams
    
    @_('empty')
    def maybeMoreActionParams(self,p):
        return col.deque()
    @_('"," numeric maybeMoreActionParams')
    def maybeMoreActionParams(self,p):
        p.maybeMoreActionParams.appendleft(numeric)
        return p.maybeMoreActionParams
    
    @_('id "." id')
    def actionName(self,p):
        return ScopedAction(p[0],p[1])
    @_("id")
    def actionName(self,p):
        return ActionID(p.id)
    
    @_('ACTION')
    def actionLiteral(self,p):
        return ActionLiteral(p.ACTION)

    #===================
    # Call Types
    #===================
    
    @_('id "." id', 'id "." CALL')
    def callName(self,p):
        return ScopedCall(p[0],p[1])
    
    @_('id')
    def callName(self,p):
        return CallID(p[0])
    @_("CALL")
    def callName(self,p):
        return Call(p[0])
    
    #===================
    # Directive Types
    #===================

    @_(*list(map(lambda x: x.upper(),NackLexer.control)))
    def directiveName(self,p):
        return Directive(p[0])

    #===================
    # Metaparams Types
    #===================
    
    @_('metaparamPair')
    def metaparams(self,p):
        return p[0]    
    @_('metaparamPair "," metaparams')
    def metaparams(self,p):
        p.metaparams.update(p.metaparamPair)
        return p.metaparams
    
    @_('id ":" numericSymbol')
    def metaparamPair(self,p):
        return {TextID(p.id) : p.numericSymbol}

    #===================
    # Registers
    #===================
    @_('"[" registerContent "]"')
    def registerType(self,p):
        return p.registerContent
    @_('regRef regOp')
    def registerContent(self,p):
        return RegisterUnaryOp(p.regRef,p.regOp)
    @_('regRef regComp regVal')
    def registerContent(self,p):
        return RegisterComparison(p.regRef,p.regVal,p.regComp)
    @_('INCREMENT','RESET')
    def regOp(self,p):
        return p[0]
    @_('EQ','LEQ','LT','GEQ','GT','NEQ')
    def regComp(self,p):
        return p[0]
    
    @_('id')
    def regRef(self,p):
        return RegisterID(p[0])
    @_('REG')
    def regRef(self,p):
        return RegisterLiteral(p.REG)
    @_('numericSymbol')
    def regVal(self,p):
        return RegisterID(p.numericSymbol)
    #===================
    
    
    @_('id','numeric')
    def numericSymbol(self,p):
        return p[0]
    @_('NUMBER','HEXNUMBER')
    def numeric(self,p):
        return IdentifierRaw(p[0])
    @_('ID')
    def id(self,p):
        return Identifier(p.ID)
    @_('LINESKIP','LINESKIP skip')
    def skip(self,p):
        if hasattr(p,"skip"): return 1+p.skip
        return 1
    @_('')
    def empty(self, p):
        pass
    #===================================================
    
if __name__ == '__main__':
    with open(r"D:\Games SSD\MHW-AI-Analysis\RathianTest\em001_00.nack") as inf:
        data = inf.read()

    lexer = NackLexer()
    tokenized = list(lexer.tokenize(data))
    parser = NackParser()
    print()
    gt = {}
    for t in tokenized:
        if t.lineno not in gt:
            gt[t.lineno] = []
        gt[t.lineno].append(t)
    #raise
    parsed = parser.parse(iter(tokenized))