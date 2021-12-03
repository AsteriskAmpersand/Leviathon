# -*- coding: utf-8 -*-
"""
Created on Mon Oct 11 02:22:25 2021

@author: Asterisk
"""
from sly import Parser
from sly.lex import Token
from pathlib import Path,WindowsPath
import collections as col
import logging
import itertools
import re

from nackLex import NackLexer
import nackStructures as abc
from compilerErrors import SemanticError
from errorHandler import ErrorManaged



def callPassing(method):
    def substructuralCall(self,*args,**kwargs):
        po = getattr(self,self.passthroughObject)
        return getattr(po,method.__name__)(*args,**kwargs)
    return substructuralCall
        
class THKModule(ErrorManaged):
    passthroughObject = "parsedStructure"
    def __init__(self,path,thkmap,scope,settings,external = False,parent = None):
        self.subfields = []
        self.inlineResolved = False
        self.settings = settings
        self.path = Path(path)
        self.tag = "THK Module [%s]"%self.path.stem
        if external:
            self.id = -1
            self.scopeName = None
            self.inlineCall = True
            self.decompilable = True
        else:
            if scope in thkmap:
                self.id = thkmap[scope]
            else:
                idData = re.match("THK_(\d+)",scope)
                if not idData:
                    raise SyntaxError("%s is not a known THK Name or on the indexed format"%scope)
                index = int(idData.groups()[0])
                self.id = index
            self.scopeName = scope
            self.inlineCall = settings.compiler.foreignGlobal if self.id == 55 else settings.compiler.inlineForeign 
            #print("InlineCall Status",path,self.inlineCall)
            self.decompilable = path is not None
        self.parent = parent
        if self.decompilable:
            if self.parent is not None:
                self.parent.inheritChildren(self)
            self.parse()
    def parse(self):
        parsedStructure = None
        if self.decompilable:
            parsedStructure = parseNack(self.path)
        self.parsedStructure = parsedStructure
        self.parsedStructure.parent = self
        self.subfields = ["parsedStructure"]
        self.inherit()
        return parsedStructure
    @callPassing
    def externalDependencies(self):pass
    @callPassing
    def returnInline(self,functionName):pass
    @callPassing
    def substituteScopes(self):pass
    @callPassing
    def createSymbolsTable(self,parsedScopes):pass
    @callPassing
    def resolveLocal(self):pass
    def dependencies(self):
        return self.parsedStructure.dependencies()
    def resolveInlines(self):
        for dependency in self.dependencies():
            dependency.resolveInlines()
        if self.decompilable:
            if not self.inlineResolved:
                self.parsedStructure.resolveInlines()
        else:
            raise SemanticError("%s [%s] is not decompilable "%(self.scopeName,self.path))
        self.inlineResolved = True
    def resolveTerminal(self):
        if self.decompilable:
            self.parsedStructure.resolveTerminal()
    def scopeStringToScopeObject(self,root,modules,namedScopes,indexedScopes):
        if self.decompilable:
            self.dependencies = self.parsedStructure.scopeStringToScopeObject(root,modules,namedScopes,indexedScopes)
        else:
            self.dependencies = []
    def resolveScopeToModule(self,modulemap):
        if self.decompilable:
            self.parsedStructure.resolveScopeToModule(modulemap)
    def mapLocalNodeNames(self):
        self.parsedStructure.mapLocalNodeNames()
    @callPassing
    def resolveActions(self,entityMap,monster):pass
    @callPassing
    def resolveCalls(self):pass
    @callPassing
    def collectRegisters(self):pass
    @callPassing
    def resolveRegisters(self,namespace):pass
    @callPassing
    def resolveFunctions(self,functionResolver):pass
    @callPassing
    def compileProperties(self):pass
    def serialize(self,outputRoot,outputName):
        self.binfile = self.parsedStructure.serialize()
        with open(outputRoot/outputName,"wb") as outf:
            outf.write(self.binfile)
    def __hash__(self):
        return hash((self.path.absolute(),-1))
    def __eq__(self,other):
        return self.path.absolute() == other.path.absolute()
    def __str__(self):
        return str(self.parsedStructure)

class NackParser(Parser):
    log = logging.getLogger()
    log.setLevel(logging.ERROR)
    # Get the token list from the lexer (required)
    tokens = NackLexer.tokens
    debugfile = 'nackParser.out'

    def parse(self,iterableTokens):
        self.file = abc.NackFile()
        t = Token()
        t.type = "LINESKIP"
        t.value = '\n'
        t.lineno = -1
        t.index = -1
        return super().parse(itertools.chain(iterableTokens,[t]))

    #===================================================
    # File
    #===================================================

    @_('nackHeader nackBody','skip nackHeader nackBody')
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
    @_('assignment nackHeader')
    def nackHeader(self,p):
        pass #handled by register declaration code
    
    @_('IMPORTLIBRARY PATH AS ID skip')
    def libraryImport(self,p):
        self.file.scopeNames[p.ID] = abc.ScopeTarget(p.PATH,"path")
    @_('IMPORTLIBRARY ID AS ID skip')
    def libraryImport(self,p):
        self.file.scopeNames[p.ID0] = abc.ScopeTarget(p.ID1,"id")
    @_('IMPORTLIBRARY numeric AS ID skip')
    def libraryImport(self,p):
        self.file.scopeNames[p.numeric] = abc.ScopeTarget(p.ID,"ix")
    
    @_('IMPORTACTIONS PATH AS ID skip')
    def actionImport(self,p):
        self.file.actionScopeNames[p[3]] = abc.ActionTarget(p[1],"path")
    @_('IMPORTACTIONS ID AS ID skip')
    def actionImport(self,p):
        self.file.actionScopeNames[p[3]] = abc.ActionTarget(p[1],"id")
    @_('REGISTER id skip')
    def registerDeclaration(self,p):
        self.file.registerNames[p.id] = None
    @_('REGISTER id AS REG skip')
    def registerDeclaration(self,p):
        self.file.registerNames[p.id] = ord(p.REG[1])-ord('A')
    @_('id ASSIGN numeric skip')
    def assignment(self,p):
        self.file.assignments[p.id.id] = p.numeric.id


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
        return abc.Node(p.defHeader,p.nodeBody+p.nodeEnd)
    
    @_('DEF id nodeAlias nodeIndex skip')
    def defHeader(self,p):
        p.nodeAlias.appendleft(p.id)
        return abc.NodeHeader(list(map(lambda x: x.id,p.nodeAlias)),
                              p.nodeIndex,p.lineno)
    
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
        s.addEndNode()
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
        return col.deque([p.uncontrolledSegment])
    @_('uncontrolledSegment')
    def segment(self,p):
        return col.deque([p.uncontrolledSegment])
    @_('UNSAFE skip')
    def segment(self,p):
        return col.deque([abc.UnsafeSegment(p.UNSAFE)])
    @_('DO_NOTHING skip')
    def segment(self,p):
        return col.deque([abc.Segment()])

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
        bd = p.chanceBody
        if len(p.optionalChance)==1: bd = bd.last()
        s.addChance(bd)
        p.nodeBody.appendleft(s)
        return p.nodeBody + p.optionalChance
    @_('optionalTerminator')
    def optionalChance(self,p):
        return col.deque([p.optionalTerminator])
    
    @_("ENDC skip",
       "ENDCHANCE skip")
    def optionalTerminator(self,p):
        s = abc.Segment()
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
        return abc.ChanceHead(p[2])
    
    @_('elsechance "(" numeric ")"',
       'elsechance "(" id ")"')
    def chanceBody(self,p):
        return abc.ChanceElse(p[2])
    
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
        return p.nodeBody + p.conditionalTerminator
    @_('ELSE actionTypeStart nodeBody conditionalTerminator')
    def conditionalTerminator(self,p):
        s = p.actionTypeStart
        s.addConditionalBranch()
        p.nodeBody.appendleft(s)
        return p.nodeBody + p.conditionalTerminator
    
    @_('ENDIF skip')
    def conditionalTerminator(self,p):
        s = abc.Segment()
        s.endConditional()
        return col.deque([s])
    @_('ENDWITH uncontrolledSegment')
    def conditionalTerminator(self,p):
        p.uncontrolledSegment.endConditional()
        return col.deque([p.uncontrolledSegment])
    
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
        return abc.Segment()
    #===================================================
    #===================================================
    # Basic Types
    #===================================================
    # Function
    @_('functionName','functionLiteral')
    def functionType(self,p):
        return p[0]
    @_('registerType')
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
        s = abc.Segment()
        s.addMeta(p.metaparams)
        return s


    #===================
    # Function Types
    #===================
    #Last string issues are here
    @_('FUNCTION_START id')
    def functionName(self,p):
        return abc.FunctionShell(p.id,[])
    @_('FUNCTION_START id parens')
    def functionName(self,p):
        return abc.FunctionShell(p.id,p.parens)
    @_('FUNCTION_START id maybeParens maybeSubFunction')
    def functionName(self,p):
        shell = abc.FunctionShell(p.id,p.maybeParens)
        shell.extend(p.maybeSubFunction)
        return shell
    
    @_('"." id maybeParens')
    def maybeSubFunction(self,p):
        return abc.FunctionShell(p.id,p.maybeParens)
    @_('"." id parens maybeSubFunction')
    def maybeSubFunction(self,p):
        shell = abc.FunctionShell(p.id,p.parens)
        shell.extend(p.maybeSubFunction)
        return shell
    
    @_('parens')
    def maybeParens(self,p):
        return p.parens
    @_('empty')
    def maybeParens(self,p):
        return ""
    
    @_('"(" ")"')
    def parens(self,p):
        return col.deque()
    @_('funcParens')
    def parens(self,p):
        return p.funcParens
    
    @_('FUNCTION maybeFuncLiteralParens')
    def functionLiteral(self,p):
        abc.FunctionLiteral(p.FUNCTION,p.maybeFuncLiteralParens)
    @_('empty')
    def maybeFuncLiteralParens(self,p):
        return []
    @_('"(" ")"')
    def maybeFuncLiteralParens(self,p):
        return []
    @_('funcParens')
    def maybeFuncLiteralParens(self,p):
        return p.funcParens
    
    #@_('empty')
    #def maybeDotID(self,p):
    #    return ''
    #@_('"." id maybeDotID')
    #def maybeDotID(self,p):
    #    return ''.join(map(str,p))

    @_('"(" id "." id commaPrefacedId ")"')
    def funcParens(self,p):
        p.commaPrefacedId.appendleft(abc.IdentifierScoped(p.id0.id,p.id1.id))
        return p.commaPrefacedId
    @_('"(" floatNumericSymbol commaPrefacedId ")"')
    def funcParens(self,p):
        p.commaPrefacedId.appendleft(p.floatNumericSymbol)
        return p.commaPrefacedId
    
    @_('empty')
    def commaPrefacedId(self,p):
        return col.deque()
    @_('"," id "." id commaPrefacedId')
    def commaPrefacedId(self,p):
        p.commaPrefacedId.appendleft(abc.MaybeScopedId(p.id0,p.id1))
        return p.commaPrefacedId
    @_('"," floatNumericSymbol commaPrefacedId')
    def commaPrefacedId(self,p):
        p.commaPrefacedId.appendleft(p.floatNumericSymbol)
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
        p.maybeMoreActionParams.appendleft(p.numeric)
        return p.maybeMoreActionParams
    
    @_('empty')
    def maybeMoreActionParams(self,p):
        return col.deque()
    @_('"," numeric maybeMoreActionParams')
    def maybeMoreActionParams(self,p):
        p.maybeMoreActionParams.appendleft(p.numeric)
        return p.maybeMoreActionParams
    
    @_('id "." id')
    def actionName(self,p):
        return abc.ScopedAction(abc.IdentifierScoped(p[0].id,p[2].id))
    @_("id")
    def actionName(self,p):
        return abc.ActionID(p.id)
    
    @_('ACTION')
    def actionLiteral(self,p):
        return abc.ActionLiteral(p.ACTION)

    #===================
    # Call Types
    #===================
    
    @_('id "." id')
    def callName(self,p):
        return abc.ScopedCallID(abc.IdentifierScoped(p[0].id,p[2].id))
    @_('id "." CALL')
    def callName(self,p):
        return abc.ScopedCall(p[0],p[2])
    
    @_('id')
    def callName(self,p):
        return abc.CallID(p[0])
    @_("CALL")
    def callName(self,p):
        return abc.Call(p[0])
    
    #===================
    # Directive Types
    #===================

    @_(*list(map(lambda x: x.upper(),NackLexer.control)))
    def directiveName(self,p):
        return abc.Directive(p[0])

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
        return {abc.TextID(p.id) : p.numericSymbol}

    #===================
    # Registers
    #===================
    @_('"[" registerContent "]"')
    def registerType(self,p):
        return p.registerContent
    @_('regRef regOp')
    def registerContent(self,p):
        return abc.RegisterUnaryOp(p.regRef,p.regOp)
    @_('regRef regComp regVal')
    def registerContent(self,p):
        return abc.RegisterComparison(p.regRef,p.regVal,p.regComp)
    @_('INCREMENT','RESET')
    def regOp(self,p):
        return p[0]
    @_('EQ','LEQ','LT','GEQ','GT','NEQ')
    def regComp(self,p):
        return p[0]
    
    @_('id')
    def regRef(self,p):
        return abc.RegisterID(p[0])
    @_('REG')
    def regRef(self,p):
        return abc.RegisterLiteral(p.REG)
    @_('numericSymbol')
    def regVal(self,p):
        return p.numericSymbol
    #===================
    
    
    @_('id','numeric')
    def numericSymbol(self,p):
        return p[0]
    @_('id','numeric','float')
    def floatNumericSymbol(self,p):
        return p[0]
    @_('FLOAT')
    def float(self,p):
        return abc.IdentifierRaw(p[0])
    @_('NUMBER','HEXNUMBER')
    def numeric(self,p):
        return abc.IdentifierRaw(p[0])
    @_('ID')
    def id(self,p):
        return abc.Identifier(p.ID)
    @_('LINESKIP','LINESKIP skip')
    def skip(self,p):
        if hasattr(p,"skip"): return 1+p.skip
        return 1
    @_('')
    def empty(self, p):
        pass
    #===================================================

def outputTokenization(tokenized):
    for t in tokenized:
        if t.type != "LINESKIP":
            print(t.type, end=' ')
        else:
            print(t.value, end= '')
            
def parseNack(file):
    #print('parseNack',file)
    with open(file,"r") as inf:
        data = inf.read() + "\n"
    lexer = NackLexer()
    tokenized = lexer.tokenize(data)
    parser = NackParser()
    parsed = parser.parse(tokenized)
    return parsed

def moduleParse(path,thkmap,scope,settings,parent = None,external = False):
    return THKModule(path,thkmap,scope,settings,parent = parent,external = external)

if __name__ == '__main__':
    with open(r"D:\Games SSD\MHW-AI-Analysis\RathianTest\em001_55.nack") as inf:
        data = inf.read()
    data2 = """
def node_040
	if function#AB() 
		function#AA() 
		>> node_039 
	else 
	endif 
	return 
endf 
    """
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