# -*- coding: utf-8 -*-
"""
Created on Tue Dec  7 08:28:56 2021

@author: Asterisk
"""
MACRO_SYMBOL = "~"

def wrappedIndex(string,index):
    try:
        return string.index(index)
    except:
        return -1

def extractName(line):
    p = line.find("(")
    if p == -1:
        raise ValueError("Malformed Macro")
    start = line[2:p]
    return line[p+1:], start.strip()

def extractArgs(line):
    p = line.find(")")
    if p == -1:
        raise ValueError("Malformed Macro")
    args = list(map(lambda x: x.strip(),line[:p].split(";")))
    return line[p+1:],args
        
class MacroReplace():
    def __init__(self,line,args):
        self.replacement = line[line.find('!')+1:].strip()
        self.args = args
        self.format = self.replacement
        for ix,arg in enumerate(self.args):
            self.format = self.format.replace(arg,"\\"+MACRO_SYMBOL*(ix+1)+"\\")
    def replace(self,arguments):
        if len(arguments)!=len(self.args):
            raise ValueError("Unmatched macro argument count")
        line = self.format
        for ix,arg in reversed(list(enumerate(arguments))):
            line = line.replace("\\"+MACRO_SYMBOL*(ix+1)+"\\",arg)
        return line
    def __repr__(self):
        return "<("+",".join(self.args)+")"+": "+self.format+">"
    
def macroBuild(line,macros):
    ix = line.find(MACRO_SYMBOL*2)
    line[ix:]
    line,token = extractName(line)
    line,args = extractArgs(line)
    replacer = MacroReplace(line,args)
    macros[token] = replacer

def macroProcess(line,macros):
    start = wrappedIndex(line,"(")
    if start == -1:
        raise ValueError("Unenclosed Macro")
    identifier = line[:start].strip()
    if identifier not in macros:
        raise ValueError("Undeclared Macro")
    replacer = macros[identifier]
    end = wrappedIndex(line,")")
    if end == -1:
        raise ValueError("Unterminated Macro")
    argstr = line[start+1:end]
    args = list(map(lambda x: x.strip(), argstr.split(";")))
    outl = replacer.replace(args)
    return line[end+1:],outl
    
def macroApply(line,macros):
    oline = ""
    while(ix := wrappedIndex(line,MACRO_SYMBOL)) >-1:
        oline += line[:ix]
        line = line[ix+1:]
        line,result = macroProcess(line,macros)
        oline += result
    oline += line
    return oline

def macroProcessor(text,display):
    macros = {}
    results = []
    for ix,line in enumerate(text.split("\n")):
        nline = ""
        if MACRO_SYMBOL*2 in line:
            try:
                macroBuild(line,macros)
            except ValueError:
                display("Line %d: Malformed Macro"%ix)
        else:
            if MACRO_SYMBOL in line:
                try:
                    nline = macroApply(line,macros)
                except ValueError as v:
                    display("Line %d: Malformed Macro Application [%s]"%(ix,str(v)))
            else:
                nline = line
        results.append(nline)
    return '\n'.join(results)

if __name__ in "__main__":
    test = '%%macroTest(arg1;arg2) ! macroTestOfaStringarg1_(arg2)\ntest\nnotHere\narg1\nmacroTest\nin here there is something %macroTest( wyz  ;  .argTest) more texxt apces\nmaybMore'
    print(test)
    print()
    print(macroProcessor(test,print))