from panda3d.core import *
from copy import deepcopy
from direct.gui.OnscreenText import OnscreenText

class OnscreenLine:
    def __init__(self, text, pos, scale, align, fg, parent, font, line = 0):
        self.textnode = OnscreenText(text = text,
                                     pos = pos,
                                     scale = scale,
                                     align = align,
                                     fg = fg,
                                     parent = parent,
                                     font = font)
        self.lineIndex = line
        self.charInterval = [0, 0] # used to determine the position of the text in the saved line

def redistribute(lines, char_limit, line_limit, textnodeList): # lines = console._SavedLines
    SavedContent = deepcopy(lines) # we want to be able to reverse ad modify the list freely
    SavedContent.reverse() # most recent lines first
    assert line_limit == len(textnodeList)
    i = 0
    l = 0 # if you want to start the reformatting from a scrolled line, change this variable
    while i < line_limit:
        if l < len(SavedContent): # avoid out of range errors when reading the data
            line = SavedContent[l][0]
            color = SavedContent[l][1]
        else:
            for t in range(i, line_limit):
                textnodeList[t].textnode.text = ""
                textnodeList[t].charInterval = [0,0]
            return 
        
        text = [line[t:t+char_limit] for t in range(0,len(line),char_limit)]
        n = len(text)
        text.reverse()
        for j in range(n):
            if i < line_limit: # idk why but the while loop sometimes isn't triggered
                textnodeList[i].textnode.text = text[j]
                textnodeList[i].textnode.fg = color
                textnodeList[i].lineIndex = len(SavedContent) - l
                previous = ''
                for t in range(j): previous+=text[t]
                textnodeList[i].charInterval = [len(previous), len(previous) + len(text[j])-1]
            i+=1
        l+=1
    return 

def displace(lines, char_limit, line_limit, textnodeList, index, delta):
    n = len(textnodeList)
    # count defined lines
    m = 0
    for x in lines:
        if not x==None:
            m+=int(len(x)%char_limit != 0) + len(x)//char_limit # count the defined lines (an undefined line would return None as lineIndex) 
    # initialize counter
    if delta == 1:
        if index + line_limit >= m: return index 
        i = 0
    elif delta == -1:
        if index <= 0: return index # reached the bottom
        i = n-1
    # loop
    while 0 <= i < n:
        if i+delta < 0 or i+delta >=n: # limit
            boolsign = delta > 0 # boolean equivalent of delta (delta equals +-1)
            if not textnodeList[i].lineIndex == None:
                chunk = lines[textnodeList[i].lineIndex][0]
                chunkcolor = lines[textnodeList[i].lineIndex][1]
            else:
                chunk = ''
                chunkcolor = (1,1,1,1)
            # splitting and formatting process
            ci = textnodeList[i].charInterval
            if boolsign and textnodeList[i].lineIndex > 0: # going up
                if ci[0] == 0: # loading new line
                    offboundstr = lines[textnodeList[i].lineIndex - delta][0]
                    offboundfg = lines[textnodeList[i].lineIndex - delta][1]
                    temp = [offboundstr[t:t+char_limit] for t in range(0,len(offboundstr),char_limit)]
                    textnodeList[i].textnode.text = temp[-1]
                    textnodeList[i].textnode.fg = offboundfg
                    textnodeList[i].lineIndex = textnodeList[i].lineIndex - delta
                    textnodeList[i].charInterval = [len(offboundstr)-len(temp[-1]),len(offboundstr)-1]
                else: # keep loading the same line                    
                    textnodeList[i].textnode.text = chunk[max(ci[0] - char_limit, 0) : ci[0]]
                    textnodeList[i].charInterval = [max(ci[0] - char_limit, 0) , ci[0]]
                    textnodeList[i].textnode.fg = chunkcolor
                    # lineIndex stays the same
            else: # going down
                if ci[1] == len(chunk) - 1: # loading new line
                    offboundstr = lines[textnodeList[i].lineIndex - delta][0] # delta is a relative int
                    offboundfg = lines[textnodeList[i].lineIndex - delta][1]
                    
                    textnodeList[i].textnode.text = offboundstr[:min(char_limit, len(offboundstr))]
                    textnodeList[i].charInterval = [0,min(char_limit-1, len(offboundstr)-1)]
                    
                    textnodeList[i].textnode.fg = offboundfg
                    textnodeList[i].lineIndex = textnodeList[i].lineIndex - delta
                else: # keep loading the same line
                    textnodeList[i].textnode.text = chunk[ci[1]+1 : min(len(chunk),ci[1]+1+char_limit)]
                    textnodeList[i].charInterval = [ci[1]+1 , min(len(chunk)-1,ci[1]+char_limit)]
                    textnodeList[i].textnode.fg = chunkcolor
                    # lineIndex stays the same
        else: # middle lines (no need to load)
            textnodeList[i].textnode.text = textnodeList[i+delta].textnode.text
            textnodeList[i].textnode.fg = textnodeList[i+delta].textnode.fg
            textnodeList[i].lineIndex = textnodeList[i+delta].lineIndex
            textnodeList[i].charInterval = textnodeList[i+delta].charInterval
        i+=delta
    index += delta
    return index

def find_all_list(element, list): # unused
    indices = []
    for i in range(len(list)):
        if element == list[i]:
            indices.append(i)
    return indices