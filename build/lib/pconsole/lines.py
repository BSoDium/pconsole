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
            m+=1+len(x)//char_limit # count the defined lines (an undefined line would return None as lineIndex) 
    # initialize counter
    if delta == 1:
        if index + line_limit >= m: return index 
        i = 0
    elif delta == -1:
        if index <= 0: return index # reached the bottom
        i = n-1
    # loop
    while 0 <= i < n:
        l = textnodeList[i]
        if 0 <= i+delta < n: # middle
            l.textnode.text = textnodeList[i+delta].textnode.text
            l.textnode.fg = textnodeList[i+delta].textnode.fg
            l.lineIndex = textnodeList[i+delta].lineIndex
            l.charInterval = textnodeList[i+delta].charInterval
        else: # limit
            boolsign = delta > 0 # boolean equivalent of delta (delta equals +-1)
            if not l.lineIndex == None:
                chunk = lines[l.lineIndex][0]
                chunkcolor = lines[l.lineIndex][1]
            else:
                chunk = ''
                chunkcolor = (1,1,1,1)
            # splitting and formatting process
            ci = l.charInterval
            if boolsign: # going up
                if ci[0] == 0: # loading new line
                    offboundstr = lines[l.lineIndex - delta][0]
                    offboundfg = lines[l.lineIndex - delta][1]
                    temp = [offboundstr[t:t+char_limit] for t in range(0,len(offboundstr),char_limit)]
                    l.textnode.text = temp[-1]
                    l.textnode.fg = offboundfg
                    l.lineIndex = l.lineIndex - delta
                    l.charInterval = [len(offboundstr)-len(temp[-1]),len(offboundstr)-1]
                else: # keep loading the same line                    
                    try: 
                        l.textnode.text = chunk[ci[0] - 1 - char_limit : ci[0] - 1]
                        l.charInterval = [ci[0] - 1 - char_limit , ci[0] - 1]
                    except IndexError:
                        l.textnode.text = chunk[:ci[0] - 1]
                        l.charInterval = [0 , ci[0] - 1]
                    l.textnode.fg = chunkcolor
                    # lineIndex stays the same
            else: # going down
                if ci[1] == len(chunk) - 1: # loading new line
                    offboundstr = lines[l.lineIndex - delta][0] # delta is a relative int
                    offboundfg = lines[l.lineIndex - delta][1]
                    try: 
                        l.textnode.text = offboundstr[:char_limit]
                        l.charInterval = [0,char_limit]
                    except IndexError:
                        l.textnode.text = offboundstr
                        l.charInterval = [0,len(offboundstr)-1]
                    l.textnode.fg = offboundfg
                    l.lineIndex = l.lineIndex - delta
                else: # keep loading the same line
                    try: 
                        l.textnode.text = chunk[ci[1]+1:ci[1]+1+char_limit]
                        l.charInterval = [ci[1]+1,ci[1]+1+char_limit]
                    except IndexError:
                        l.textnode.text = chunk[ci[1]+1:]
                        l.charInterval = [ci[1]+1,len(chunk)-1]
                    l.textnode.fg = chunkcolor
                    # lineIndex stays the same
        i+=delta
    index += delta
    return index

def find_all_list(element, list):
    indices = []
    for i in range(len(list)):
        if element == list[i]:
            indices.append(i)
    return indices