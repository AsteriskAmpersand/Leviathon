# -*- coding: utf-8 -*-
"""
Created on Sun Dec  5 00:51:04 2021

@author: Asterisk
"""

import argparse
import sys
from pathlib import Path
from Leviathon.compiler.compiler import fandCompile,nackCompile
from Leviathon.compiler.compilerSettings import CompilerSettings
from Leviathon.common.fexLayer import buildCompiler
from Leviathon.common.actionEnum import loadActionMaps,loadTHKMaps
from Leviathon.common.monsterEnum import loadEntities

def generateArgParse():
    parser = argparse.ArgumentParser(description='Leviathon Compiler')
    parser.add_argument('input', type=str,
                        help='Project file to compile (.fand)')
    
    parser.add_argument('verbose', action="store_false",
                        help='Print intermediate compilation process information')
    parser.add_argument('display', type=str,  default = "",
                        help='Output compilation reports to the given file')
    
    parser.add_argument('monLib', type=str, default = None,
                        help='Override Default Monster Library')
    parser.add_argument('fexty', type=str,  default = None,
                        help='Override Default Function Resolver (.fexty)')
    parser.add_argument('thkNames', type=str,  default = None,
                        help='Override Default THK Names')    
    parser.add_argument('directForeign', action="store_false",
                        help='Use Direct Reference to Foreign Imports instead of inlining')
    parser.add_argument('inlineGlobal', action="store_true",
                        help='Inline Global Functions')
    
    parser.add_argument('preprocessor', type=bool, default = False,
                        help='[Non-Standard] Run the macro prepropcessor')
    
    parser.add_argument('forceCritical', action="store_true",                        
                        help='Convert all errors into critical errors that automatically stop compilation')
    parser.add_argument('forceError', action="store_true",
                        help='Convert all warnings into errors')
    parser.add_argument('repeatedProperty', type=str,  default = "Warning",
                        help='Error level for repeated properties [Warning,Error,CriticalError]')


    parser.add_argument('outputName', type=str,  default = "em000",
                        help='Output THKList Name')
    parser.add_argument('outputRoot', type=str, default = "",
                        help='Output Folder')
    return parser

def buildSettings(args):
    settings = CompilerSettings()
    settingsRemap = {"verbose":"verbose","display":"display", 
                     "monLib":"entityMap" , 
                     "fexty": "functionResolver" , 'thkNames':"thkMap", 
                     "directForeign":"inlineForeign", "inlineGlobal":"foreignGlobal" ,
                     "preprocessor":"preprocessor" , 
                     "forceCritical":"forceCritical" , "forceError":"forceError" ,
                     "repeatedProperty": 'repeatedProperty', 
                     "outputName":"thklistPath" , "outputRoot":"outputRoot"                     
                     }
    for setting in settingsRemap:
        setattr(settings.decompiler,settingsRemap[setting],getattr(args,setting))
    return settings
    
def pickCompiler(inputFile,settings):
    extension = Path(inputFile).suffix
    compilers = {'.fand':fandCompile,".nack":nackCompile}
    if extension not in compilers:
        raise ValueError("%s is not a .fand or .nack file"%inputFile)
    comp = compilers[extension]
    return comp

def main():
    parser = generateArgParse()    
    args = parser.parse_args(sys.argv[1:])
    
    settings = buildSettings(args)
    
    if settings.entityMap is None:
        actionResolver = loadActionMaps()
    else:
        actionResolver = loadActionMaps(settings.entityMap)
    entityResolver = loadEntities(actionResolver)
    settings.entityMap = entityResolver
    
    if settings.functionResolver is None:
        settings.functionResolver = buildCompiler().resolve    
    else:
        settings.functionResolver = buildCompiler(settings.functionResolver).resolve    

    compiler = pickCompiler(args.input,settings)
    compiler(args.input,settings)
    
if __name__ in "__main__":
    main()