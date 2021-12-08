# -*- coding: utf-8 -*-
"""
Created on Sun Oct 10 19:11:45 2021

@author: Asterisk
"""
from sly import Lexer
import regex
import common.keywords as key
from common.registerOperations import (sUnaryOperators, sUnaryNames,
                                       sBinaryOperators, sBinaryNames)


def slyRegex(pattern, *extra):
    patterns = [pattern, *extra]

    def decorate(func):
        pattern = '|'.join(f'({pat})' for pat in patterns)
        if hasattr(func, 'pattern'):
            func.pattern = pattern + '|' + func.pattern
        else:
            func.pattern = pattern
        return func
    return decorate


def atomicCapture(regexp):
    def inner(f):
        @slyRegex(regexp)
        def newfunction(self, t):
            path = regex.match(regexp, t.value).groups()[0]
            t.value = path
            return f(self, t)
        return newfunction
    return inner


def tokenEscape(token):
    return token  # regex.escape(token)

    
class NackLexer(Lexer):

    literals = {'(', ')', '{', '}', '[', ']', ":", ".", ",", "&"}

    directives = [key.REGISTER, key.IMPORTACT, key.IMPORTLIB, key.AS]
    control = [key.RETURN, key.RESET, key.REPEAT]
    node_keywords = [key.DEF, key.ENDF, key.ENDF2, key.ENDF3]
    chance_keywords = [key.RANDOM, key.ELSER, key.ELSER2,
                       key.ENDR, key.ENDR2, key.ENDRW, key.ENDRW2]
    if_keywords = [key.IF, key.ELSE, key.ELIF, key.ENDIF, key.ENDIFW]
    init_keywords = [key.ENDALL]
    id_keywords = {keyword: keyword.upper()
                   for keyword in sum([directives, control, node_keywords, chance_keywords, if_keywords, init_keywords], [])}
    reg_unary_keywords = {**{regex.escape(op): name for op, name in zip(sUnaryOperators, sUnaryNames)},
                          **{regex.escape(op): name for op, name in zip(sBinaryOperators, sBinaryNames)}}
    tokens = {*id_keywords.values(), *reg_unary_keywords.values(),
              FUNCTION_START, LINECONTINUE, LINESKIP, COMMENTS, DO_ACTION, DO_CALL, DO_DIRECTIVE, DO_NOTHING,
              META, REG, PATH,
              UNSAFE, FLOAT, NUMBER, HEXNUMBER, ACTION, FUNCTION, CALL, ID,
              ASSIGN, DORRAH}

    @_('//.*')
    def COMMENTS(self,t): return
    
    FUNCTION_START = "self."
    LINECONTINUE = r'\\.*\n'
    DO_ACTION = key.DO_ACTION
    DO_CALL = key.DO_CALL
    DO_DIRECTIVE = key.DO_DIRECTIVE
    DO_NOTHING = key.DO_NOTHING
    META = key.META
    
    #explicit register
    @atomicCapture(r"\$([A-V])")
    def REG(self,t): 
        t.value = ord(t.value) - ord('A')
        return t

    ignore = ' \t'

    # unsafe
    @_(r"%s [\s0-9A-Fa-f]+" % key.UNSAFE)
    def UNSAFE(self, t):
        match = regex.match(r"%s ([\s0-9A-Fa-f]+)" %
                            key.UNSAFE, t.value).groups()[0]
        t.value = int(match.replace(" ", "").replace("\t", ""), 16)
        return t

    # number
    @_(r"-?[0-9]+\.[0-9]+")
    def FLOAT(self, t):
        t.value = float(t.value)
        return t
    # number

    @_(r"-?[0-9]+")
    def NUMBER(self, t):
        t.value = int(t.value)
        return t

    # hexnumber
    @_(r"0x[0-9A-F]+")
    def HEXNUMBER(self, t):
        t.value = int(t.value, 16)
        return t

    @atomicCapture("%s[#]([0-9a-fA-F]+)" % key.ACTION)
    def ACTION(self, t):
        t.value = int(t.value, 16)
        return t

    @atomicCapture("%s[#]([0-9a-fA-F]+)" % key.FUNCTION)
    def FUNCTION(self, t):
        t.value = int(t.value, 16)
        return t

    @atomicCapture("%s[#]([0-9])+" % key.CALL)
    def CALL(self, t):
        t.value = int(t.value, 10)
        return t

    #Register Directives have to go here to not overshadwo the Calls
    CLEAR = '\|\-'
    INCREMENT = '\+\+'
    DECREMENT = '\-\-'
    TIME = '\#\#'
    ELAPSED = '\#\-'
    EQ = '=='
    LEQ = '<='
    LT = '<'
    GEQ = '>='
    GT = '>'
    NEQ = '!='
    ADD = '\+='
    SUB = '\-='
    MUL = '\*='
    DIV = '/='
    MOD = '%='
    ELAPGT = '\#>'
    ELAPLT = '\#<'
    
    ASSIGN = "="

    @_(r'".*"')
    def PATH(self, t):
        t.value = t.value.replace('"', "")
        return t

    @_(r"[a-zA-Z_][a-zA-Z'_0-9]*")
    def ID(self, t):
        # Check for reserved words
        t.type = self.id_keywords.get(t.value, 'ID')
        return t

    # Line number tracking
    @_(r';|\n+')
    def LINESKIP(self, t):
        self.lineno += t.value.count('\n')
        return t
    # [RegisterName Comparison/Asignment Value/Variable]

    def error(self, t):
        print('Line %d: Bad character %r' % (self.lineno, t.value[0]))
        self.index += 1


def produceRegisterKeywords():
    reg_unary_keywords = {**{regex.escape(op): name for op, name in zip(sUnaryOperators, sUnaryNames)},
                          **{regex.escape(op): name for op, name in zip(sBinaryOperators, sBinaryNames)}}
    for regexp, name in reg_unary_keywords.items():
        print("\t%s = '%s'" % (name, regexp))
