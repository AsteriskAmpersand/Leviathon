# -*- coding: utf-8 -*-
"""
Created on Wed Jul  1 17:57:04 2020

@author: AsteriskAmpersand
"""

import construct as c
from pathlib import Path
from operator import itemgetter
from itertools import groupby

#import sqlite3
#conn = sqlite3.connect(':memory:')

Header = c.Struct(
        "signature" / c.Const([84,72,75,0],c.Byte[4]),
        "formatVersion" / c.Const(40,c.Int16sl),
        "structCount" / c.Int16sl,
        "unknownHash" / c.Int32ub,
        "isPalico" / c.Int32sl,
        "monsterID" / c.Int64sl,
        "headerSize" / c.Const(32,c.Int64sl)
        )


_Segment = c.Struct(
        "endRandom" / c.Byte,#if 0x40 checkFunction is 0
        "flowControl" / c.Byte,
        "branchingControl" / c.Byte,
        "unkn1" / c.Byte,#NULL
        "unkn2" / c.Int32sl,#NULL
        "functionType" / c.Int32sl,#ifs can't have a 00 on checkType,
        "parameter1" / c.Int32sl,
        "unkn3" / c.Int32sl,#2,3,5(9,52) in the checkType for when 20_0000 40_0000 80_0000 100_0000, only used by ems
        "unkn4" / c.Int32sl,#80_0000 20_0000 40_0000
        "comboSetting" / c.Int32sl,#00,02 as checktype when 100 1 2
        "unkn6" / c.Int32sl,#00 02 as checkType when 8000 10000
        "parameter2" / c.Int32sl,
        "nodeEndingData" / c.Int32sl,#Only used when End Random is 1, and is equal to Node Index + 10 000
        "extRefThkID" / c.Int32sl,#0x55 for external, -1 otherwise
        "extRefNodeID" / c.Int32sl,#-1 when unused
        "localRefNodeID" / c.Int64sl,#-1 when unused
        "unkn7" / c.Int32sl,#NULL
        "unkn8" / c.Int32sl,#NULL
        "unkn9" / c.Int32sl,#NULL
        "unkn10" / c.Int32sl,#NULL
        "unkn11" / c.Int32sl,
        "actionID" / c.Int32sl,
        "actionUnkn0" / c.Int32sl,
        "actionUnkn1" / c.Int32sl,
        "actionUnkn2" / c.Int32sl,
        "unkn12" / c.Int32sl,
        "actionUnkn3" / c.Int32sl,
        "actionUnkn4" / c.Int32sl,
        "unknExtra0" / c.Int32sl,  
        "unknExtra1" / c.Int32sl,  
        "unknExtra2" / c.Int32sl,
        "monsterID" / c.Computed(lambda this : this._._.header.monsterID),
        "isPalico" / c.Computed(lambda this : this._._.header.isPalico),
        )
Segment = c.Aligned(0x8,_Segment)
#Equip segments with is otomo, monster ID for checks

#Node ends are always of the form of all values nulled except endRandom at 1 and the nodeEndingData being set at the appropiate value


hiddenColumns = ["unkn7","unkn8","unkn9","unkn10","unkn1","unkn2","type","subtype","subspecies","offset","count","id"]

Node = c.Struct(
        "offset" / c.Int64ul,
        "count" / c.Int32ul,
        "id" / c.Int32ul,
        "segments" / c.Pointer(c.this.offset,Segment[c.this.count])
        )

Thk = c.Struct(
        "header" / Header,
        "nodeList" / Node[c.this.header.structCount]
        )

if __name__ in "__main__":
    import pandas as pd
    chunk = Path(r"D:\Games SSD\MHW\chunk")
    
    def iterable(ob):
        try:
            iter(ob)
            return True
        except:
            return False
    
    fileColumns = ("fileId","path","type","subtype","subspecies","file")
    nodeNames = [f.name for f in Node.subcons[:-1]]
    nodeColumns = ("nodeId","fileId",*nodeNames)
    segmentNames = [f.name for f in _Segment.subcons[:-1]]
    segmentColumns = ("segmentId","fileId","nodeId",*segmentNames)
    wholeColumns = ("path","type","subtype","subspecies","file","node","segment",*nodeNames,*segmentNames)
    
    files = []
    nodes = []
    segments = []
    whole = []
    
    flowControls = {}
    #from collections import defaultdict
    #hashes = defaultdict(set)
    for kx,thk in enumerate(chunk.rglob("*.thk")):#[Path(r"E:\MHW\chunkG0\otomo\ot210\data\ot210_31.thk")]:#
        file = Thk.parse_stream(thk.open("rb"))
        relative = thk.relative_to(chunk)
        #hashes["%08X"%file.header.unknownHash].add(relative)
        #continue
        raise
        pathing = [relative,relative.parts[0],relative.parts[1],relative.parts[2],relative.stem]
        fileEntry = (kx,*pathing)
        files.append(fileEntry)
        for ix,node in enumerate(file.nodeList):
            nodeFields = [list(getattr(node,f.name)) if iterable(getattr(node,f.name)) else getattr(node,f.name)
                                    for f in Node.subcons[:-1]]
            nodeEntry = (ix,kx,*nodeFields)
            nodes.append(nodeEntry)
            for jx,segment in enumerate(node.segments):
                segmentFields = [list(getattr(segment,f.name)) if iterable(getattr(segment,f.name)) else getattr(segment,f.name)
                                            for f in Segment.subcons[:-1]]
                segmentEntry = (jx,kx,ix,*segmentFields)   
                segments.append(segmentEntry)
                wholeEntry = (*pathing,ix,jx,*nodeFields,*segmentFields)
                whole.append(wholeEntry)
    #for hashing in hashes:
    #    print(hashing)
    #    print('\n'.join(["\t"+str(h) for h in sorted(hashes[hashing])]))
    #raise
    f = pd.DataFrame(data = files, columns = fileColumns)
    n = pd.DataFrame(data = nodes, columns = nodeColumns)
    s = pd.DataFrame(data = segments, columns = segmentColumns)
    w = pd.DataFrame(data = whole, columns = wholeColumns)
    
    thkf = r"D:\MHW Modding\Wisdom\thkFiles.csv"
    thkn = r"D:\MHW Modding\Wisdom\thkNodes.csv" 
    thks = r"D:\MHW Modding\Wisdom\thkSegmt.csv"
    thkw = r"D:\MHW Modding\Wisdom\thkWhole.csv"
    
    f.to_csv(thkf)
    n.to_csv(thkn)
    s.to_csv(thks)
    w.to_csv(thkw)
    
    w0 = w.drop(hiddenColumns,axis = 1)
    def simplifyColumn(colName):
        return ''.join([colName[0],*[char for char in colName if char.upper() == char or char in ["0","1","2","3","4","5","6","7","8","9"]]])
    w0 = w0.rename(simplifyColumn,axis = 1)
    
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    
    
    # =============================================================================
    # raise
    # with open(r"G:\Wisdom\unknownCheckType.json","w") as outf:
    #     for typing in sorted(flowControls,key = lambda x: (len(set(flowControls[x][0])),x)):
    #         #print()
    #         outf.write('"0x%04X":{\n'%typing)
    #         
    #         fc = flowControls[typing]
    #         for file,group in groupby(fc,key=itemgetter(0)):
    #             outf.write("\t"+'"'+str(file.relative_to(chunk))+'"'+":{")
    #             outf.write(", ".join(['"%03d/%03d"'%(ix,jx) for f, ix, jx in group]))
    #             outf.write("},\n")
    #         outf.write('},\n')
    # 
    # =============================================================================
