# -*- coding: utf-8 -*-
"""
Created on Fri Oct  8 17:44:24 2021

@author: Asterisk
"""

# fexlex.py

from sly import Lexer
from sly.lex import Token
from Leviathon.common.thk import Segment


class FexLexer(Lexer):
    accessor = {c.name:c.name.upper() for c in Segment.subcons}
    enums = {'st_enum' : "STAGE_ENUM",
             'em_enum' : "MONSTER_ENUM",
             'float_cast' : "FLOAT_CAST"}
    id_keywords = {**accessor,**enums,"otherwise":"FALLTHROUGH"}
    
    # Set of token names.   This is always required
    tokens = { HEXUSE,PREFACEDHEX,EQ,#NUMBER,
              PREFIX,NUMBER,ID,NEWLINE,PASS,
              *id_keywords.values()}


    literals = { '(', ')', '{', '}', '.',',','>',':'}
    
    def __init__(self):
        self.nesting_level = 0
        self.hexmode = False
         
    @_(r"Use Hex")
    def HEXUSE(self,t):
        return t

    # String containing ignored characters
    ignore = ' \t'

    # Regular expression rules for tokens        
    @_(r'pass(\s|\n|\r)+')
    def PASS(self, t):
        t.value = ""
        return t

    @_(r'0x[0-9A-F]+')
    def PREFACEDHEX(self, t):
        t.value = int(t.value,16)
        return t
    """
    @_(r'[0-9]+(?![a-zA-Z_])')
    def NUMBER(self, t):
        if self.hexmode:
            t.value = int(t.value,16)
        else:
            t.value = int(t.value)
        return t
    """

    #FLOAT = r'\d*\.\d+'
    EQ      = r'=='

    @_(r'\{')
    def lbrace(self, t):
        t.type = '{'      # Set token type to the expected literal
        self.nesting_level += 1
        return t

    @_(r'\}')
    def rbrace(self,t):
        t.type = '}'      # Set token type to the expected literal
        self.nesting_level -=1
        return t

    # Identifiers and keywords
    @_(r'[a-zA-Z_0-9]+')
    def ID(self,t):
        t.type = self.id_keywords.get(t.value,'ID') 
        return t
    
    
    ignore_comment = r'\#.*'

    # Line number tracking
    @_(r'\n+')
    def NEWLINE(self, t):
        self.lineno += t.value.count('\n')
        return t

    def error(self, t):
        print('Line %d: Bad character %r' % (self.lineno, t.value[0]))
        self.index += 1

class ExtensibleToken(Token):
    pass

def clone(tok):
    tok2 = ExtensibleToken()
    tok2.type = tok.type
    tok2.value = tok.value
    tok2.lineno = tok.lineno
    tok2.index = tok.index
    if hasattr(tok,"hexmode"):
        tok2.hexmode = tok.hexmode
    return tok2

def constructPreface(t_iter):
    preface = []
    t = next(t_iter)
    while t.type != 'NEWLINE':
        preface.append(t)
        t = next(t_iter)
    return preface

def assignPreface(t_iter,t,preface):
    result = []
    while t.type != ":":
        result.append(t)
        t = next(t_iter)
    result.append(t)
    def assign(x):
        x = clone(x)
        x.lineno = t.lineno
        return x
    result += list(map(lambda x: assign(x), preface))
    return result

def linkPreface(t):
    result = []
    if t.type == "PASS":
        lparens = Token()
        lparens.type = "("
        lparens.value = "("
        lparens.lineno = t.lineno
        lparens.index = t.index
        result.append(lparens)
        rparens = Token()
        rparens.type = ")"
        rparens.value = ")"
        rparens.lineno = t.lineno
        rparens.index = t.index
        result.append(rparens)
        t.type = "NEWLINE"
        t.value = "\n"
    else:
        dot = Token()
        dot.type = "."
        dot.value = "."
        dot.lineno = t.lineno
        dot.index = t.index
        result.append(dot)
    return result

def macroPrefix(t_iter):
    result = []
    preface = constructPreface(t_iter)
    t = next(t_iter)
    while t.type != '}':
        result += assignPreface(t_iter,t,preface)
        t = next(t_iter)
        if t.type != "(":
            result += linkPreface(t)
        while t.type != "NEWLINE":
            result.append(t)
            t = next(t_iter)
        result.append(t)
        t = next(t_iter)
        #print(t)
    result.append(t)
    return result

def preproc(tokens):
    #Remove Hex Use and all initial newlines
    #expand Prefix occurernces to all of the elements after
    t_iter = iter(tokens)
    result = []
    for t in t_iter:            
        if t.type == ">":
            result += macroPrefix(t_iter)
        else:
            result.append(t)
    return result
        

if __name__ == '__main__':
    data = '''
Use Hex
3{
  >targetEnemy
  parameter1 == 1 : (target_em.random_player_or_cat)
  parameter1 == 2 : (target_em.closest_entity)
  parameter1 == 13 : (target_em.last_attacker)
  parameter1 == 29 : (target_em.any_monster)
  parameter1 == 41 : (target_em.nearest_monster)
  parameter1 == 66 : (target_em.last_target)
}
4: targetUnknown(parameter1,parameter2)
0x2E{
	>target
	parameter1 == 0x5: helpless_0()
	parameter1 == 0x6: helpless_1()
	parameter1 == 0x2D: mudded()
	otherwise : pass 
}
5{parameter1 == 1 : (target_em.random_player_or_cat)}
'''
    #with open("test.fexty") as inf:
    #    data = inf.read()
    lexer = FexLexer()
    tokenized = list(lexer.tokenize(data))
    tokens = preproc( [ tok for tok in tokenized])
    for tok in tokens:
        print(tok)