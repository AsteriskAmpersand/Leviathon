# -*- coding: utf-8 -*-
"""
Created on Sun Dec  5 00:51:04 2021

@author: Asterisk
"""

import argparse
import sys
from pathlib import Path
from compiler.compiler import fandCompile,nackCompile
from compiler.compilerSettings import CompilerSettings
from common.fexLayer import buildCompiler
from common.actionEnum import loadActionMaps,loadTHKMaps
from common.monsterEnum import loadEntities

def generateArgParse():
    parser = argparse.ArgumentParser(description='Leviathon Compiler')
    parser.add_argument('input', nargs = 1, type=str, 
                        help='Project file to compile (.fand)')
    parser.add_argument('-verbose', action="store_false",
                        help='Print intermediate compilation process information')
    parser.add_argument('-display', type=str,  default = "",
                        help='Output compilation reports to the given file')
    
    parser.add_argument('-monLib', type=str, default = None,
                        help='Override Default Monster Library')
    parser.add_argument('-fexty', type=str,  default = None,
                        help='Override Default Function Resolver (.fexty)')
    parser.add_argument('-thkNames', type=str,  default = None,
                        help='Override Default THK Names')    
    parser.add_argument('-directForeign', action="store_false",
                        help='Use Direct Reference to Foreign Imports instead of inlining')
    parser.add_argument('-inlineGlobal', action="store_true",
                        help='Inline Global Functions')
    parser.add_argument('-projectNames', type=str, default='index',
                        choices=["function","nackfile","index"])
    #parser.add_argument('-deduplicate', action="store_true",
    #                    help='Export each scope as a separate file')
    
    parser.add_argument('-preprocessor', type=bool, default = False,
                        help='[Non-Standard] Run the macro prepropcessor')
    
    parser.add_argument('-forceCritical', action="store_true",                        
                        help='Convert all errors into critical errors that automatically stop compilation')
    parser.add_argument('-forceError', action="store_true",
                        help='Convert all warnings into errors')
    parser.add_argument('-repeatedProperty', type=str,  default = "Warning",
                        help='Error level for repeated properties [Warning,Error,CriticalError]')


    parser.add_argument('-outputName', type=str,  default = "em000.thklst",
                        help='Output THKList Name')
    parser.add_argument('-outputRoot', type=str, default = None,
                        help='Output Folder')
    return parser

def buildSettings(args):
    settings = CompilerSettings()
    settingsRemap = {"verbose":"verbose","display":"display", 
                     "monLib":"entityMap" , 
                     "fexty": "functionResolver" , 'thkNames':"thkMap", 
                     "directForeign":"inlineForeign", "inlineGlobal":"foreignGlobal" ,
                     "projectNames":"projectNames",#"deduplicate":"deduplicateModules",
                     "preprocessor":"preprocessor" , 
                     "forceCritical":"forceCritical" , "forceError":"forceError" ,
                     "repeatedProperty": 'repeatedProperty', 
                     "outputName":"thklistPath" , "outputRoot":"outputRoot",
                     }
    for setting in settingsRemap:
        setattr(settings,settingsRemap[setting],getattr(args,setting))
    return settings
    
def pickCompiler(inputFile,settings):
    extension = Path(inputFile).suffix
    compilers = {'.fand':fandCompile,".nack":nackCompile}
    if extension not in compilers:
        raise ValueError("%s is not a .fand or .nack file"%inputFile)
    comp = compilers[extension]
    return comp

def populateSettings(settings,inputF):
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
    if settings.thkMap is None:
        settings.thkMap = loadTHKMaps().moduleToThk
    else:
        settings.thkMap = loadTHKMaps(settings.thkMap).moduleToThk
    if settings.outputRoot is None:
        settings.outputRoot = Path(inputF).parent/"compiled"
    settings.outputRoot.mkdir(parents=True, exist_ok=True)

def main(arglist):
    parser = generateArgParse()    
    args = parser.parse_args(arglist)
    args.input = args.input[0]
    settings = buildSettings(args)
    populateSettings(settings,args.input)
    compiler = pickCompiler(args.input,settings)
    compiler(args.input,settings)
    
if __name__ in "__main__":
    main(sys.argv[1:])