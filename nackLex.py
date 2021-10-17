# -*- coding: utf-8 -*-
"""
Created on Sun Oct 10 19:11:45 2021

@author: Asterisk
"""
from sly import Lexer
import keywords as key
class NackLexer(Lexer):
    
    literals = { '(', ')', '{', '}', '[', ']',":",".","&"}
    
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
              INCREMENT,RESET,EQ,LEQ,LT,GEQ,GT,NEQ}
    COMMENTS = '//.*'
    FUNCTION_START = "self."
    LINECONTINUE = r'\\.*\n'
    LINESKIP = r';|\n'
    DO_ACTION = key.DO_ACTION
    DO_CALL = key.DO_CALL
    DO_DIRECTIVE = key.DO_DIRECTIVE
    DO_NOTHING = key.DO_NOTHING
    META = key.META
    
    #explicit register
    REG = r"$[A-T]"
    
    #unsafe
    UNSAFE = r"%s [\s0-9A-Fa-f]+"%key.UNSAFE
    
    #number
    NUMBER = r"[0-9]+"
    
    #hexnumber
    HEXNUMBER = r"0x[0-9A-F]+"
    
    ACTION = "%s#[0-9a-fA-F]+"%key.ACTION
    FUNCTION = "%s#[0-9a-fA-F]+"%key.FUNCTION
    CALL = "%s#[0-9]+"%key.CALL
    
    #RegisterOperators
    INCREMENT = "\+\+"
    RESET = "\|-"
    
    EQ = "=="
    LEQ = "<="
    LT = "<"
    GEQ = ">="
    GT = ">"
    NEQ = "!="
    
    PATH = r'".*"'
        
    @_(r"[a-zA-Z_][a-zA-Z'_0-9]*")
    def ID(self,t):
        t.type = self.id_keywords.get(t.value,'ID')    # Check for reserved words
        return t
    
    #[RegisterName Comparison/Asignment Value/Variable]
    


