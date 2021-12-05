# -*- coding: utf-8 -*-
"""
Created on Fri Oct 22 21:00:01 2021

@author: Asterisk
"""


import logging
import regex as re
from sly import Lexer,Parser
from compiler.fandStructure import FandStructure

T_COMMENTS = r'//.*'
T_ROOT = "at"
T_RELATIVE = "through"
T_MONSTER = "is"
T_REGISTER = "Register"
T_ALIAS = "as"
T_ASSIGN = '='
T_ENTRY_COUNT = "has"
T_SELECTIVE_IMPORT = "from"
T_SELECTION = "using"
T_QUALIFIED_IMPORT = "uses"
T_INDEXER = ":"
T_SPECIFIER = "@"
T_NUMERIC = "\d+"
T_HEXNUMERIC = "[0-9A-Fa-f]*"
T_ID = r"[a-zA-Z_][a-zA-Z'_0-9]*"
T_PATH = r"[^\s^@^\n][^@^\n]*[^\s^\n^@]"

parens = lambda x: "("+x+")"

comments = T_COMMENTS
root = T_ROOT + "\s+" + parens(T_PATH)
relative = (T_RELATIVE) + "\s+" + parens(T_PATH)
monster = (T_MONSTER) + "\s+" + parens(T_PATH)
register_alias = T_ALIAS + "\s+" + parens("$[A-T]")
register = T_REGISTER + "\s+" + parens(T_PATH)
indexer = T_INDEXER + parens(T_NUMERIC)
specifier = (T_SPECIFIER) + "\s*" + parens(T_HEXNUMERIC)
assign = parens(T_ID)+ "\s+" +T_ASSIGN+ "\s+" +parens(T_PATH)
entry_count = T_ENTRY_COUNT+ "\s+" + parens(T_NUMERIC) + ".*"
selective_import = T_SELECTIVE_IMPORT + "\s+" + parens(T_PATH) + "\s+" + T_SELECTION + "\s+" + parens(T_ID)
qualified_import = T_QUALIFIED_IMPORT + parens(T_PATH) + "\s+" + T_ALIAS + "\s+" + parens(T_ID)

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
            path = re.match(regexp,t.value).groups()[0]
            t.value = path
            return f(self,t)
        return newfunction
    return inner

def binaryCapture(regexp):
    def inner(f):
        @slyRegex(regexp)
        def newfunction(self,t):
            source,target = re.match(regexp,t.value).groups()
            t.value = (source,target)
            return f(self,t)
        return newfunction
    return inner

class FandLexer(Lexer):
    literals = { '(', ')', '{', '}', '[', ']'}
    tokens = {COMMENTS,ROOT,RELATIVE,MONSTER,REGISTER_ALIAS,REGISTER,SPECIFIER,INDEXER,
              ASSIGN,ENTRY_COUNT,SELECTIVE_IMPORT,QUALIFIED_IMPORT,LINESKIP}
    ignore = " \t"
    COMMENTS = comments
    
    @atomicCapture(root)
    def ROOT(self,t):return t
    @atomicCapture(relative)
    def RELATIVE(self,t):return t
    @atomicCapture(monster)
    def MONSTER(self,t):return t
    @atomicCapture(register_alias)
    def REGISTER_ALIAS(self,t):return t
    @atomicCapture(register)
    def REGISTER(self,t):return t
    @atomicCapture(specifier)
    def SPECIFIER(self,t):
        t.value = int(t.value,16)
        return t
    @atomicCapture(indexer)
    def INDEXER(self,t):
        t.value = int(t.value)
        return t
    @atomicCapture(entry_count)
    def ENTRY_COUNT(self,t):
        t.value = int(t.value)
        return t
    @binaryCapture(assign)
    def ASSIGN(self,t):return t
    @binaryCapture(selective_import)
    def SELECTIVE_IMPORT(self,t):return t
    @binaryCapture(qualified_import)
    def QUALIFIED_IMPORT(self,t):return t
    
    @_(r';|\n+')
    def LINESKIP(self, t):
        self.lineno += t.value.count('\n')
        return t

class FandParser(Parser):
    tokens = FandLexer.tokens
    log = logging.getLogger()
    log.setLevel(logging.ERROR)

    def parse(self,*args,**kwargs):
        self.file = FandStructure()
        return super().parse(*args,**kwargs)

    @_('maybeSkip maybeRoot RELATIVE skip maybeMonster body maybeEntryCount maybeSkip')
    def fandFile(self,p):
        self.file.relative = p.RELATIVE
        return self.file
    
    @_('empty')
    def maybeRoot(self,p):
        return
    @_('ROOT skip')
    def maybeRoot(self,p):
        self.file.root = p.ROOT
        return 
    
    @_('empty')
    def maybeMonster(self,p):
        return
    @_('MONSTER skip')
    def maybeMonster(self,p):
        self.file.monster = p.MONSTER
        return
    
    @_('empty')
    def maybeEntryCount(self,p):
        return
    @_('ENTRY_COUNT')
    def maybeEntryCount(self,p):
        self.file.count = p.ENTRY_COUNT
        return 
    
    @_('empty')
    def body(self,p):
        return
    @_('registerDeclaration skip body')
    def body(self,p):
        return
    @_('ASSIGN maybeSpecifier skip body')
    def body(self,p):
        self.file.scopeNames[p.ASSIGN[0]] = p.ASSIGN[1]
        self.file.unindexedTargets[p.ASSIGN[0]] = (p.ASSIGN[0],p.ASSIGN[1],p.maybeSpecifier)
        return
    @_('ASSIGN INDEXER maybeSpecifier skip body')
    def body(self,p):
        self.file.scopeNames[p.ASSIGN[0]] = p.ASSIGN[1]
        self.file.indexedTargets[p.INDEXER] = (p.ASSIGN[0],p.ASSIGN[1],p.maybeSpecifier)    
        return
    
    @_('REGISTER REGISTER_ALIAS')
    def registerDeclaration(self,p):
        self.file.registerNames[p.REGISTER] = ord(p.REGISTER_ALIAS[1].upper()) - ord('A')
        return
    @_('REGISTER')
    def registerDeclaration(self,p):
        self.file.registerNames[p.REGISTER] = None
        return
    
    @_('empty')
    def maybeSpecifier(self,p):
        return None
    @_('SPECIFIER')
    def maybeSpecifier(self,p):
        return p.SPECIFIER
    
    @_('empty')
    def maybeSkip(self,p):
        return
    @_('skip')
    def maybeSkip(self,p):
        return
    
    @_('LINESKIP')
    def skip(self,p):
        return
    
    @_('')
    def empty(self,p):
        return
    
def parseFand(file):
    with open(file,"r") as inf:
        data = inf.read()+"\n"
    lexer = FandLexer()
    tokenized = lexer.tokenize(data)
    parser = FandParser()
    parsed = parser.parse(tokenized)
    return parsed
    

if __name__ in "__main__":
    with open(r"D:\Games SSD\MHW-AI-Analysis\Leviathon\tests\ingameFiles\ems062_02_data\ems062.fand") as inf:
        data = inf.read()
    lexer = FandLexer()
    tokenized = list(lexer.tokenize(data))
    print()
    gt = {}
    for t in tokenized:
        print(t)
    parser = FandParser()
    parsed = parser.parse(iter(tokenized))
    