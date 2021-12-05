# -*- coding: utf-8 -*-
"""
Created on Sat Oct  9 15:06:26 2021

@author: Asterisk
"""

from sly import Parser
import logging
from collections import deque
import struct

from Leviathon.common.fexLex import FexLexer,preproc
from Leviathon.common.stageEnum import loadStages
from Leviathon.common.monsterEnum import loadEntities

st_enum = loadStages()
em_enum = loadEntities()

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

castOperators = {"float_cast":lambda x: struct.unpack('<i', struct.pack('<f', x))[0]}
#TODO - Import names from actual scope
#and find a better resolution mechanism
enumScopes = {"em_enum":em_enum,"st_enum":st_enum}

class Accessors(deque):
    def match(self,target):
        return all([accessor.match(var) for accessor,var in zip(self,target)])
    def parse(self,target):
        return [(accessor.field,accessor.parse(var)) for accessor,var in zip(self,target)]
class Accessor():
    def __init__(self,field,transformType = None,transformData = None):
        self.field = field
        self.transformType = transformType
        self.transformData = transformData
    def __str__(self):
        return self.field if self.transformType is None\
            else self.transformData+"."+self.field
    def __repr__(self):
        if self.transformType is not None:
            return "__{%s:%s}__"%(self.transformData,self.field)
        else:
            return "__%s__"%self.field
    def copy(self):
        a = Accessor(self.field,self.transformType,self.transformData)
        return a
    def split(self):
        return self.field,self.transformType,self.transformData
    def match(self,var):
        #"ENUM", "CAST", None, 
        #float_cast em_enum st_enum
        if self.transformType is None:
            return hasattr(var,"raw_id") and var.raw_id is not None
        if self.transformType == "CAST":
            return hasattr(var,"raw_id") and var.raw_id is not None
        if self.transformType == "ENUM":
            return var.verifyEnum(enumScopes[self.transformData])
    def parse(self,var):
        if self.transformType is None:
            return var.raw_id
        if self.transformType == "CAST":
            return castOperators[self.transformData](var.raw_id)
        if self.transformType == "ENUM":
            return var.accessEnum(enumScopes[self.transformData])
        
class EnumStruct():
    def __init__(self,idVal):
        self.chain = [idVal]
    def prepend(self,scope):
        self.chain = [scope] + self.chain
        return self
    def __str__(self):
        return '.'.join(self.chain)
    def __repr__(self):
        return str(self)
    def __len__(self):
        return 1
    def match(self,target):
        return str(self) == '.'.join(map(str,target))
    def parse(self,target):
        return []
class Empty():
    def __str__(self):
        return ""
    def __len__(self):
        return 0
    def __repr__(self):
        return str(self)
    def match(self,target):
        return not target
    def parse(self,target):
        return []
class Target(deque):
    def __init__(self):
        self.types = deque()
        super().__init__()        
    def prepend(self,data,typing):
        self.types.appendleft(typing)
        self.appendleft(data)
        return self
    def functionalStructure(self):
        previous = ""
        fields = []
        dataTypes = []
        dataIndices = []
        strCumul = []
        cumulative = ""
        for typing,data in zip(self.types,self):
            if typing == "literal":
                if previous not in {"literal","enum"}:
                    cumulative = ""
                if previous:
                    cumulative += "."
                cumulative += str(data)
            elif typing == "accessors":
                field,dtt,dti = map(list,zip(*map(lambda x: x.split(), data)))
                fields.append(field)
                dataTypes.append(dtt)
                dataIndices.append(dti)
                strCumul.append(cumulative)   
                cumulative = ""
            elif typing == "enum":
                cumulative += "(" + str(data) + ")"
            previous = typing
        return fields,dataTypes,dataIndices,strCumul,cumulative
    def signature(self):
        return tuple([-1 if t == "literal" else len(data) for t,data in zip(self.types,self) ])
    def literalSignature(self):
        return tuple([str(data) for t,data in zip(self.types,self) if t == "literal"])
    def exactMatch(self,target):
        args = [(typing,data) for typing,data in zip(self.types,self) if typing != "literal"]
        for t,(typing,data) in zip(target.params,args):
            if not data.match(t):
                return False
        return True#
    def parse(self,target):
        result = []
        args = [(typing,data) for typing,data in zip(self.types,self) if typing != "literal"]
        for t,(typing,data) in zip(target.params,args):
            result += data.parse(t)
        return result
            
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
        t = Target()
        return t.prepend(p.ID,"literal")
    #Target
    @_('ID "." target')
    def target(self, p):
        return p.target.prepend(p.ID,"literal")  
    #Target
    @_('ID parens')
    def target(self, p):
        t = Target()
        return t.prepend(*p.parens).prepend(p.ID,"literal")
    #Target
    @_('ID parens "." target')
    def target(self, p):
        return p.target.prepend(*p.parens).prepend(p.ID,"literal")
    
    @_('"(" ")"')
    def parens(self, p):
        return (Empty(),"enum")
    @_('"(" enumable ")"')
    def parens(self, p):
        return (p.enumable,"enum")
    @_('"(" accessors ")"')
    def parens(self, p):
        return (p.accessors,"accessors")
    
    @_('ID')
    def enumable(self, p):
        return EnumStruct(p.ID)
    @_('ID "." enumable')
    def enumable(self, p):
        return p.enumable.prepend(p.ID)
    
    @_('accessor')
    def accessors(self, p):
        return Accessors([p.accessor])
    @_('accessor "," accessors')
    def accessors(self, p):
        p.accessors.appendleft(p.accessor)
        return p.accessors

    @_('EQ')
    def comparison(self, p):
        return p.EQ

    # Enum
    @_('"{" MONSTER_ENUM ":" raw_accessor "}"',
       '"{" STAGE_ENUM ":" raw_accessor "}"')
    def enum(self, p):
        return Accessor(p.raw_accessor.field,"ENUM",p[1])
    
    
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
        return Accessor(p.raw_accessor.field,"CAST","float")

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
    with open("default.fexty") as inf:
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
        pass
        #print(t)
    #raise
    parsed = parser.parse(iter(tokens))