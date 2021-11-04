# -*- coding: utf-8 -*-
"""
Created on Sun Oct 10 19:11:45 2021

@author: Asterisk
"""
from sly import Lexer
import keywords as key
import regex

def slyRegex(pattern, *extra):
    patterns = [pattern, *extra]
    def decorate(func):
        pattern = '|'.join(f'({pat})' for pat in patterns )
        if hasattr(func, 'pattern'):
            func.pattern = pattern + '|' + func.pattern
        else:
            func.pattern = pattern
        return func
    return decorate

def atomicCapture(regexp):
    def inner(f):
        @slyRegex(regexp)
        def newfunction(self,t):
            path = regex.match(regexp,t.value).groups()[0]
            t.value = path
            return f(self,t)
        return newfunction
    return inner

class NackLexer(Lexer):
    
    literals = { '(', ')', '{', '}', '[', ']',":",".",",","&"}
    
    directives = [ key.REGISTER, key.IMPORTACT, key.IMPORTLIB, key.AS ]
    control = [ key.RETURN, key.RESET, key.REPEAT ]
    node_keywords = [ key.DEF, key.ENDF, key.ENDF2, key.ENDF3 ]
    chance_keywords = [key.CHANCE, key.ELSEC, key.ELSEC2, key.ENDC, key.ENDC2, key.ENDCW, key.ENDCW2] 
    if_keywords = [key.IF, key.ELSE, key.ELIF, key.ENDIF, key.ENDIFW]
    init_keywords = [key.ENDALL]
    id_keywords = {keyword:keyword.upper() 
                   for keyword in sum([directives,control,node_keywords,chance_keywords,if_keywords,init_keywords],[])}
    
    tokens = {*id_keywords.values(),
              FUNCTION_START,LINECONTINUE,LINESKIP,COMMENTS,DO_ACTION,DO_CALL,DO_DIRECTIVE,DO_NOTHING,
              META,REG,PATH,
              UNSAFE,NUMBER,HEXNUMBER,ACTION,FUNCTION,CALL,ID,
              INCREMENT,RESET,EQ,LEQ,LT,GEQ,GT,NEQ,
              ASSIGN}
    
    @_('//.*')
    def COMMENTS(self,t): return
    
    FUNCTION_START = "self."
    LINECONTINUE = r'\\.*\n'
    DO_ACTION = key.DO_ACTION
    DO_CALL = key.DO_CALL
    DO_DIRECTIVE = key.DO_DIRECTIVE
    DO_NOTHING = key.DO_NOTHING
    META = key.META
    
    ignore = ' \t'
    
    #explicit register
    @atomicCapture(r"$([A-T])")
    def REG(self,t): 
        t.value = ord(t.value) - ord('A')
        return t
    
    #unsafe
    @_(r"%s [\s0-9A-Fa-f]+"%key.UNSAFE)
    def UNSAFE(self,t):
        match = regex.match(r"%s ([\s0-9A-Fa-f]+)"%key.UNSAFE,t.value).groups()[0]
        t.value = int(match.replace(" ","").replace("\t",""),16)
        return t
    
    #number
    @_(r"-?[0-9]+")
    def NUMBER(self,t):
        t.value = int(t.value)
        return t
    
    #hexnumber
    @_(r"0x[0-9A-F]+")
    def HEXNUMBER(self,t):
        t.value = int(t.value,16)
        return t
    
    @atomicCapture("%s[#]([0-9a-fA-F]+)"%key.ACTION)
    def ACTION(self,t): 
        t.value = int(t.value,16)
        return t
    @atomicCapture("%s[#]([0-9a-fA-F]+)"%key.FUNCTION)
    def FUNCTION(self,t): 
        t.value = int(t.value,16)
        return t
    @atomicCapture("%s[#]([0-9])+"%key.CALL)
    def CALL(self,t): 
        t.value = int(t.value,10)
        return t
    
    #RegisterOperators
    INCREMENT = "\+\+"
    RESET = "\|-"
    
    EQ = "=="
    LEQ = "<="
    LT = "<"
    GEQ = ">="
    GT = ">"
    NEQ = "!="
    ASSIGN = "="
    PATH = r'".*"'
        
    @_(r"[a-zA-Z_][a-zA-Z'_0-9]*")
    def ID(self,t):
        t.type = self.id_keywords.get(t.value,'ID')    # Check for reserved words
        return t
    
    # Line number tracking
    @_(r';|\n+')
    def LINESKIP(self, t):
        self.lineno += t.value.count('\n')
        return t
    #[RegisterName Comparison/Asignment Value/Variable]
    
    def error(self, t):
        print('Line %d: Bad character %r' % (self.lineno, t.value[0]))
        self.index += 1
