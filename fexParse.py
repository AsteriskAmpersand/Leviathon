# -*- coding: utf-8 -*-
"""
Created on Sat Oct  9 15:06:26 2021

@author: Asterisk
"""

from sly import Parser
from fexLex import FexLexer,preproc
import logging

class EntryStructure(dict):
    def resolveNumeric(self,hexcoded = False):
        newMapping = []
        for key,val in self.items():
            numericKey = key.resolveNumeric(hexcoded)
            resolvedList = []
            for pk,kval in val.items():
                nk = tuple(map(lambda x: x.resolveNumeric(hexcoded),pk))
                resolvedList.append((nk,kval))
            newMapping.append((numericKey,dict(resolvedList)))
        return dict(newMapping)

class DeferredInt():
    def __init__(self,intval = "0"):
        self.intstring = intval
        self.value = None
    def resolveNumeric(self,hexcoded):
        self.value = int(self.intstring,16 if hexcoded else 10)
        return self.value
    def __str__(self):
        return str(self.value)
    def __hash__(self):
        return hash(self.intstring)
    
class Accessor():
    def __init__(self,field,transformType = None,transformData = None):
        self.field = [field]
        self.transformType = [transformType]
        self.transformData = [transformData]
        self.string = [""]
        self.term = ""
    def __str__(self):
        result = ""
        for s,f,tt,td in zip(self.string,self.field,self.transformType,self.transformData):
            if tt is not None:
                result += s + "__{%s:%s}__"%(td,f)
            else:
                result += s + "__%s__"%f 
        return result + self.term
    def __repr__(self):
        return str(self)
    def copy(self):
        a = Accessor(0)
        a.string = self.string
        a.field = self.field
        a.transformType = self.transformType
        a.transformData = self.transformData
        a.term = self.term
        return a
    #self + op
    def __add__(self,op):
        a = self.copy()
        if type(op) is str:
            a.term += op
        else:
            a.field += op.field
            a.transformType += op.transformType
            a.transformData += op.transformData
            a.string.append(self.term + op.string[0])
            a.string += op.string[1:]
            a.term = op.term
        return a
    #op + self
    def __radd__(self,op):
        a = self.copy()
        if type(op) is str:
            a.string[0] = op + a.string[0]
        else:
            raise ValueError("Unsuported Type")
            #a.field = op.field + a.field
            #a.transformType = op.transformType + a.transformType
            #a.transformData = op.transformData + a.transformData
            #a.string[0] = op.term+a.string[0]
            #a.string = op.string + a.string
        return a

class Condition():
    def __init__(self,maybeAccessor,comparison,maybeNumeric):
        if type(maybeAccessor) is Accessor:
            self.accessor = maybeAccessor
            self.comparison = comparison
            self.numeric = maybeNumeric
        else:
            self.accessor = maybeNumeric
            self.comparison = comparison
            self.numeric = maybeAccessor
    def __str__(self):
        return str(self.accessor) + self.comparison + str(self.numeric)
    def __repr__(self):
        return str(self)
    def resolveNumeric(self,hexcoded):
        if type(self.numeric) is DeferredInt:
            self.numeric = self.numeric.resolveNumeric(hexcoded)
        return self
    def __hash__(self):
        return hash((self.accessor,self.comparison,self.numeric))
            
class FexParser(Parser):
    # Get the token list from the lexer (required)
    tokens = FexLexer.tokens
    log = logging.getLogger()
    log.setLevel(logging.ERROR)

    @_('split HEXUSE split fextFile')
    def file(self,p):
        return EntryStructure(p.fextFile).resolveNumeric(True)
    @_('fextFile')
    def file(self,p):
        return EntryStructure(p.fextFile).resolveNumeric()

   
    @_('full fextFile',
       'inline fextFile')
    def fextFile(self, p):
        return [p[0]] + p.fextFile
    @_('')
    def fextFile(self, p):
        return []

    #Inline Expression
    @_(' number ":" target split')
    def inline(self, p):
        return (p.number,{():p.target})

    #Full Expression
    @_(' number "{" split fexprBlock "}" split')
    def full(self, p):
        return (p.number,dict(p.fexprBlock))
    @_(' number "{" split fexprBlock fallthrough split "}" split')
    def full(self, p):
        d = dict(p.fexprBlock)
        d.update(dict(p.fallthrough))
        return (p.number,d)

    #Full Expression Block
    @_('expr split fexprBlock')
    def fexprBlock(self, p):
        return [p.expr] + p.fexprBlock
    #Full Expression Block
    @_('expr split')
    def fexprBlock(self, p):
        return [p.expr]
    
    #Fallthrough
    @_('FALLTHROUGH ":" target')
    def fallthrough(self, p):
        return [((),p.target)]

    #Expression
    @_('condition ":" target')
    def expr(self, p):
        return (tuple(p.condition),p.target)

    #Condition
    @_('accessor comparison number')
    def condition(self, p):
        return [Condition(p.accessor,p.comparison,p.number)]
    #Condition
    @_('accessor comparison number "," condition')
    def condition(self, p):
        return [Condition(p.accessor,p.comparison,p.number)]+p.condition

    #Target
    @_('ID')
    def target(self, p):
        return p
    #Target
    @_('ID "." target')
    def target(self, p):
        return p.ID+"."+p.target    
    #Target
    @_('ID parens')
    def target(self, p):
        return p.ID+p.parens
    #Target
    @_('ID parens "." target')
    def target(self, p):
        return p.ID + p.parens+"."+p.target
    
    @_('"(" ")"')
    def parens(self, p):
        return "()"
    @_('"(" enumable ")"')
    def parens(self, p):
        return "(" + p.enumable + ")"
    @_('"(" accessors ")"')
    def parens(self, p):
        return "(" + p.accessors + ")"    
    
    @_('ID')
    def enumable(self, p):
        return p.ID
    @_('ID "." enumable')
    def enumable(self, p):
        return p.ID + "." + p.enumable
    
    @_('accessor')
    def accessors(self, p):
        return p.accessor
    @_('accessor "," accessors')
    def accessors(self, p):
        return p.accessor + p.accessors

    @_('EQ')
    def comparison(self, p):
        return p.EQ

    # Enum
    @_('"{" MONSTER_ENUM ":" raw_accessor "}"',
       '"{" STAGE_ENUM ":" raw_accessor "}"')
    def enum(self, p):
        return Accessor(p.raw_accessor.field[0],"ENUM",p[1])
    
    
    @_('PREFACEDHEX')
    def number(self, p):
        return p
    @_('NUMBER')
    def number(self, p):
        return p
    @_('ID')
    def number(self, p):
        #idp.value = int(p.ID,16 if self.hexmode else 10)
        return DeferredInt(p.ID)
    
    # Cast
    @_('"{" FLOAT_CAST ":" raw_accessor "}"')
    def cast(self, p):
        return Accessor(p.raw_accessor.field[0],"CAST","float")

    @_("raw_accessor","cast","enum")
    def accessor(self, p):
        return p[0]

    @_(*FexLexer.accessor.values())
    def raw_accessor(self, p):
        return Accessor(p[0])

    # Cast
    @_('NEWLINE split')
    def split(self, p):
        return
    
    # Cast
    @_('')
    def split(self, p):
        return

def buildParser(path):
    with open(path) as inf:
        data = inf.read()
    lexer = FexLexer()
    tokenized = list(lexer.tokenize(data))
    tokens = preproc([ tok for tok in tokenized])
    parser = FexParser()
    parsed = parser.parse(iter(tokens))
    return parsed

if __name__ == '__main__':
    with open("test.fexty") as inf:
        data = inf.read()
    lexer = FexLexer()
    tokenized = list(lexer.tokenize(data))
    tokens = preproc([ tok for tok in tokenized])

    parser = FexParser()
    print()
    gt = {}
    for t in tokenized:
        if t.lineno not in gt:
            gt[t.lineno] = []
        gt[t.lineno].append(t)
        
    g = {}
    for t in tokens:
        if t.lineno not in g:
            g[t.lineno] = []
        g[t.lineno].append(t)
    for t in tokens:
        print(t)
    #raise
    parsed = parser.parse(iter(tokens))