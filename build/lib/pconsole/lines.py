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

def redistribute(lines, char_limit, line_limit, textnodelist): # lines = console._SavedLines
    """
    Organize the lines and allow them to fit in the terminal window.
    """
    saved_content = deepcopy(lines) # we want to be able to reverse ad modify the list freely
    saved_content.reverse() # most recent lines first
    assert line_limit == len(textnodelist)
    i = 0
    l = 0 # if you want to start the reformatting from a scrolled line, change this variable
    while i < line_limit:
        if l < len(saved_content): # avoid out of range errors when reading the data
            line = saved_content[l][0]
            color = saved_content[l][1]
        else:
            for t in range(i, line_limit):
                textnodelist[t].textnode.text = ""
                textnodelist[t].charInterval = [0,0]
            return 
        
        text = [line[t:t+char_limit] for t in range(0,len(line),char_limit)]
        n = len(text)
        text.reverse()
        for j in range(n):
            if i < line_limit: 
                textnodelist[i].textnode.text = text[j]
                textnodelist[i].textnode.fg = color
                textnodelist[i].lineIndex = len(saved_content) - l
                previous = ''
                for t in range(j): previous+=text[t]
                textnodelist[i].charInterval = [len(previous), len(previous) + len(text[j])-1]
            i+=1
        l+=1

def displace(lines, char_limit, line_limit, textnodelist, index, delta):
    n = len(textnodelist)
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
            if not textnodelist[i].lineIndex == None:
                chunk = lines[textnodelist[i].lineIndex][0]
                chunkcolor = lines[textnodelist[i].lineIndex][1]
            else:
                chunk = ''
                chunkcolor = (1,1,1,1)
            # splitting and formatting process
            ci = textnodelist[i].charInterval
            if boolsign and textnodelist[i].lineIndex > 0: # going up
                if ci[0] == 0: # loading new line
                    offboundstr = lines[textnodelist[i].lineIndex - delta][0]
                    offboundfg = lines[textnodelist[i].lineIndex - delta][1]
                    temp = [offboundstr[t:t+char_limit] for t in range(0,len(offboundstr),char_limit)]
                    textnodelist[i].textnode.text = temp[-1]
                    textnodelist[i].textnode.fg = offboundfg
                    textnodelist[i].lineIndex = textnodelist[i].lineIndex - delta
                    textnodelist[i].charInterval = [len(offboundstr)-len(temp[-1]),len(offboundstr)-1]
                else: # keep loading the same line                    
                    textnodelist[i].textnode.text = chunk[max(ci[0] - char_limit, 0) : ci[0]]
                    textnodelist[i].charInterval = [max(ci[0] - char_limit, 0) , ci[0]]
                    textnodelist[i].textnode.fg = chunkcolor
                    # lineIndex stays the same
            else: # going down
                if ci[1] == len(chunk) - 1: # loading new line
                    offboundstr = lines[textnodelist[i].lineIndex - delta][0] # delta is a relative int
                    offboundfg = lines[textnodelist[i].lineIndex - delta][1]
                    
                    textnodelist[i].textnode.text = offboundstr[:min(char_limit, len(offboundstr))]
                    textnodelist[i].charInterval = [0,min(char_limit-1, len(offboundstr)-1)]
                    
                    textnodelist[i].textnode.fg = offboundfg
                    textnodelist[i].lineIndex = textnodelist[i].lineIndex - delta
                else: # keep loading the same line
                    textnodelist[i].textnode.text = chunk[ci[1]+1 : min(len(chunk),ci[1]+1+char_limit)]
                    textnodelist[i].charInterval = [ci[1]+1 , min(len(chunk)-1,ci[1]+char_limit)]
                    textnodelist[i].textnode.fg = chunkcolor
                    # lineIndex stays the same
        else: # middle lines (no need to load)
            textnodelist[i].textnode.text = textnodelist[i+delta].textnode.text
            textnodelist[i].textnode.fg = textnodelist[i+delta].textnode.fg
            textnodelist[i].lineIndex = textnodelist[i+delta].lineIndex
            textnodelist[i].charInterval = textnodelist[i+delta].charInterval
        i+=delta
    index += delta
    return index

def find_all_list(element, list): # unused
    indices = []
    for i in range(len(list)):
        if element == list[i]:
            indices.append(i)
    return indices