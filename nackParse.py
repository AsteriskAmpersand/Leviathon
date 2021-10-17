# -*- coding: utf-8 -*-
"""
Created on Mon Oct 11 02:22:25 2021

@author: Asterisk
"""
from sly import Parser
from nackLex import NackLexer
import logging


class NackParser(Parser):
    log = logging.getLogger()
    log.setLevel(logging.ERROR)
    # Get the token list from the lexer (required)
    tokens = NackLexer.tokens
    debugfile = 'nackParser.out'

    #===================================================
    # File
    #===================================================

    @_('nackHeader nackBody')
    def nackFile(self,p):
        pass
    
    
    @_('empty')
    def nackHeader(self,p):
        pass
    @_('libraryImport nackHeader')
    def nackHeader(self,p):
        pass
    @_('actionImport nackHeader')
    def nackHeader(self,p):
        pass
    @_('registerDeclaration nackHeader')
    def nackHeader(self,p):
        pass
    
    @_('IMPORTLIBRARY PATH AS ID skip')
    def libraryImport(self,p):
        pass
    @_('IMPORTLIBRARY ID AS ID')
    def libraryImport(self,p):
        pass
    @_('IMPORTLIBRARY numeric AS ID')
    def libraryImport(self,p):
        pass
    
    @_('IMPORTACTIONS PATH AS ID skip','IMPORTACTIONS ID AS ID skip')
    def actionImport(self,p):
        pass
    @_('REGISTER id skip')
    def registerDeclaration(self,p):
        pass
    @_('REGISTER id AS REG skip')
    def registerDeclaration(self,p):
        pass
    
    @_('node nackBody')
    def nackBody(self,p):
        pass
    @_('empty')
    def nackBody(self,p):
        pass

    #===================================================
    # Node
    #===================================================
    
    @_('defHeader nodeBody nodeEnd')
    def node(self,p):
        pass
    
    @_('DEF id nodeAlias nodeIndex skip')
    def defHeader(self,p):
        pass
    
    @_('"&" id nodeAlias')
    def nodeAlias(self,p):
        pass
    @_('empty')
    def nodeAlias(self,p):
        pass

    @_('":" numeric')
    def nodeIndex(self,p):
        pass  
    @_('":" numeric META numeric')
    def nodeIndex(self,p):
        pass  
    @_('META numeric')
    def nodeIndex(self,p):
        pass    
    @_('empty')
    def nodeIndex(self,p):
        pass    
    
    @_('segment nodeBody')
    def nodeBody(self,p):
        pass
    @_('empty')
    def nodeBody(self,p):
        pass
    
    @_('ENDF skip',
       'ENDDEF skip',
       'ENDFUNCTION skip')
    def nodeEnd(self,p):
        pass    

    #===================================================
    # Segment
    #===================================================

    @_('chance')
    def segment(self,p):
        return
    @_('conditional')
    def segment(self,p):
        return
    @_('CONCLUDE uncontrolledSegment')
    def segment(self,p):
        return
    @_('uncontrolledSegment')
    def segment(self,p):
        return
    @_('UNSAFE skip')
    def segment(self,p):
        return
    @_('DO_NOTHING skip')
    def segment(self,p):
        return

    #===================================================
    # Chance
    #===================================================
    @_('chanceHeader uncontrolledSegment segments chanceBody uncontrolledSegment optionalChance')
    def chance(self,p):
        return
    
    @_('chanceBody uncontrolledSegment segments optionalChance',
       'optionalTerminator')
    def optionalChance(self,p):
        return
    
    @_("ENDC skip",
       "ENDCHANCE skip",
       "ENDCWITH uncontrolledSegment skip",
       "ENDCHANCEWITH uncontrolledSegment skip")
    def optionalTerminator(self,p):
        return
    
    @_('CHANCE "(" numeric ")"',
       'CHANCE "(" ID ")"')
    def chanceHeader(self,p):
        return
    
    @_('elsechance "(" numeric ")"',
       'elsechance "(" ID ")"')
    def chanceBody(self,p):
        return
    
    @_('ELSECHANCE','ELSEC')
    def elsechance(self,p):
        return
    
    #===================================================
    #===================================================
    # Conditionals
    #===================================================
    @_('IF uncontrolledSegment segments conditionalTerminator')
    def conditional(self,p):
        return
    
    @_('ELIF functionType callTypeStart segments conditionalClose')
    def conditionalTerminator(self,p):
        return
    @_('ELSE callTypeStart segments conditionalClose')
    def conditionalTerminator(self,p):
        return
    
    @_('ENDIF skip')
    def conditionalClose(self,p):
        return
    @_('ENDWITH uncontrolledSegment')
    def conditionalClose(self,p):
        return
    
    #===================================================
    #===================================================
    # Basic Segments
    #===================================================
    @_('uncontrolledSegment segments')
    def segments(self,p):
        return
    @_('empty')
    def segments(self,p):
        return
    
    @_('maybeFunctionType maybeActionType maybeCallType maybeDirectiveType maybeMetaType skip')
    def uncontrolledSegment(self,p):
        return
    @_('directiveName maybeMetaType skip')
    def uncontrolledSegment(self,p):
        return
    @_('maybeCallType maybeDirectiveType maybeMetaType skip')
    def callTypeStart(self,p):
        return
    
    @_('functionType')
    def maybeFunctionType(self,p):
        return
    @_('empty')
    def maybeFunctionType(self,p):
        return
    
    @_('actionType')
    def maybeActionType(self,p):
        return
    @_('empty')
    def maybeActionType(self,p):
        return
    
    @_('callType')
    def maybeCallType(self,p):
        return
    @_('empty')
    def maybeCallType(self,p):
        return
    
    @_('directiveType')
    def maybeDirectiveType(self,p):
        return
    @_('empty')
    def maybeDirectiveType(self,p):
        return
    
    @_('metaType')
    def maybeMetaType(self,p):
        return
    @_('empty')
    def maybeMetaType(self,p):
        return
    #===================================================
    #===================================================
    # Basic Types
    #===================================================
    
    # Function
    @_('functionName','functionLiteral','registerType')
    def functionType(self,p):
        pass
    
    # Action
    @_('DO_ACTION actionName actionParens','DO_ACTION actionLiteral actionParens')
    def actionType(self,p):
        pass
    
    # Call
    @_('DO_CALL callName')
    def callType(self,p):
        pass

    # Directive
    @_('DO_DIRECTIVE directiveName')
    def directiveType(self,p):
        pass

    # Meta
    @_('META metaparams')
    def metaType(self,p):
        pass


    #===================
    # Function Types
    #===================
    #TODO - Hell
    @_('FUNCTION_START id')
    def functionName(self,p):
        pass
    @_('FUNCTION_START id parens')
    def functionName(self,p):
        pass
    @_('FUNCTION_START id maybeParens maybeSubFunction')
    def functionName(self,p):
        pass
    
    @_('"." id maybeParens')
    def maybeSubFunction(self,p):
        pass
    @_('"." id parens maybeSubFunction')
    def maybeSubFunction(self,p):
        pass
    
    @_('parens')
    def maybeParens(self,p):
        pass
    @_('empty')
    def maybeParens(self,p):
        pass
    
    @_('"(" ")"')
    def parens(self,p):
        pass
    @_('funcParens')
    def parens(self,p):
        pass
    
    @_('FUNCTION maybeFuncParens')
    def functionLiteral(self,p):
        pass
    
    @_('empty')
    def maybeFuncParens(self,p):
        pass
    @_('funcParens')
    def maybeFuncParens(self,p):
        pass
    
    @_('empty')
    def maybeDotID(self,p):
        pass
    @_('"." id maybeDotID')
    def maybeDotID(self,p):
        pass
    
    @_('"(" id "." id maybeDotID ")"')
    def funcParens(self,p):
        pass
    @_('"(" numericSymbol commaPrefacedId ")"')
    def funcParens(self,p):
        pass
    
    @_('empty')
    def commaPrefacedId(self,p):
        pass
    @_('"," numericSymbol commaPrefacedId')
    def commaPrefacedId(self,p):
        pass

    #===================
    # Action Types
    #===================
    
    @_('"(" maybeActionParams ")"')
    def actionParens(self,p):
        pass
    @_('empty','numeric maybeMoreActionParams')
    def maybeActionParams(self,p):
        pass
    @_('empty','"," numeric maybeMoreActionParams')
    def maybeMoreActionParams(self,p):
        pass
    
    @_('id "." id',"id")
    def actionName(self,p):
        pass
    
    @_('ACTION')
    def actionLiteral(self,p):
        pass

    #===================
    # Call Types
    #===================
    
    @_('id "." id', 'id "." CALL')
    def callName(self,p):
        pass
    
    @_('id',"CALL")
    def callName(self,p):
        pass
    
    #===================
    # Directive Types
    #===================

    @_(*list(map(lambda x: x.upper(),NackLexer.control)))
    def directiveName(self,p):
        pass

    #===================
    # Metaparams Types
    #===================
    
    @_('metaparamPair')
    def metaparams(self,p):
        pass    
    @_('metaparamPair "," metaparams')
    def metaparams(self,p):
        pass
    
    @_('id ":" numericSymbol')
    def metaparamPair(self,p):
        pass

    #===================
    # Registers
    #===================
    @_('"[" registerContent "]"')
    def registerType(self,p):
        pass
    @_('regRef regOp')
    def registerContent(self,p):
        pass
    @_('regRef regComp regVal')
    def registerContent(self,p):
        pass
    @_('INCREMENT','RESET')
    def regOp(self,p):
        pass
    @_('EQ','LEQ','LT','GEQ','GT','NEQ')
    def regComp(self,p):
        pass
    @_('id','REG')
    def regRef(self,p):
        pass
    @_('numericSymbol')
    def regVal(self,p):
        pass
    #===================
    
    
    @_('id','numeric')
    def numericSymbol(self,p):
        pass
    @_('NUMBER','HEXNUMBER')
    def numeric(self,p):
        pass
    @_('ID')
    def id(self,p):
        pass
    @_('LINESKIP','LINESKIP skip')
    def skip(self,p):
        pass
    @_('')
    def empty(self, p):
        pass
    #===================================================