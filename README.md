# Leviathon
![Project Logo](https://github.com/AsteriskAmpersand/Leviathon/blob/main/assets/Leviathon.fw.png?raw=true)
A simple language and reference decompiler/compiler for MHW THK Files.

## Project Goals
The project aims to define a language specification for working with THK and THKLST files as code. In that sense it aims to be a mid-level language abstraction of the low-level language which the THK comprise, providing higher level features such as named functions, action name resolution, importable behavior libraries and behavior frameworks.

The Leviathon language consists of three formats:

## Fandirus (Fand) Files

Fand files are project definitions (which are decompiled from THKLST files). They define what file is tied to which behavior group. Their structure is defined on the Fand Specification File.

Fand files are named after Fandirus, AI Research Pioneer who established most of the basis of what's known about the execution of the thk format and author of the biggest AI editing project in MHW (MHWI: Stories mod).

## NackDN (Nack) Files

Nack files are the Think Table decompilation results. They define the AI of a monster for a given context (In-Combat, Out-Of-Comabt, Turf War). Their Structure is defined on the Nack Specification File.

Nack files are named after NackDN, human repository of THK files knowledge and documentation. He formalized and documented a considerable amount of Fandirus loose findings, and more importantly authored the THK Graphical Editor Tool for THK Research without which this project wouldn't even have been started.

## Forked Functional Extension (FExtY) Files

FExtY files are dynamical language extensions which enable the compiler and decompiler to elegantly resolve THK Function Types into human readable code and viceversa. Their structure is defined on the FExtY Specification File.

FExtY files are named after Fexty, a relative newcommer to Monster AI Editing Research who performed vital decompilation and documentation work of the game internal switch cases functions as well as authored the AI Extension Framework to enable modders to add custom Function Types (which can be compatibilized with this tool through the FExtY files).

## Aditional Credits
Monster THK editing is a rich and storied field which has had numerous contributors, it's almost impossible to provide an extensive listing of findings per credit as the early history is riddled with undocumented findings and oral tradition. In chronological order:

- hexhexhex
- Fandirus
- NekotagaYuhatora
- Freschu
- NackDN
- AsteriskAmpersand
- Stracker
- Fexty

## Special Thanks
Additional credit is given to Fandirus, NackDN, Silvris and Fexty for assisting with the language specification and target feature list.

# The ABC Reference Compiler-Decompiler
<img src="https://github.com/AsteriskAmpersand/Leviathon/blob/main/assets/CompilerLogo.fw.png?raw=true" alt="Compiler Logot" width=450>

A reference Compiler-Decompiler which implements the Leviathon Specification is provided for actual practical usage. 

The compiler and decompiler are written in Python using the Construct library for binary parsing. 
A full list of of the available commands and documentation of the compilation process is planned.


