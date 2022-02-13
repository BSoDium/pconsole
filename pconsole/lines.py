from copy import deepcopy
from direct.gui.OnscreenText import OnscreenText

class OnscreenLine:
    def __init__(self, text, pos, scale, align, fg, parent, font, line = 0):
        """
        Constructs and returns a new :class:`OnscreenLine`.
        """
        self.textnode = OnscreenText(text = text,
                                     pos = pos,
                                     scale = scale,
                                     align = align,
                                     fg = fg,
                                     parent = parent,
                                     font = font)
        self.line_index = line
        self.char_interval = [0, 0] # used to determine the position of the text in the saved line

def redistribute(lines : list, char_limit : int, line_limit : int, textnodes : list) -> None: # lines = console._SavedLines
    """
    Organize the lines and allow them to fit in the terminal window.
    """
    saved_content = deepcopy(lines) # we want to be able to reverse ad modify the list freely
    saved_content.reverse() # most recent lines first
    assert line_limit == len(textnodes)
    i = 0
    l = 0 # if you want to start the reformatting from a scrolled line, change this variable
    while i < line_limit:
        if l < len(saved_content): # avoid out of range errors when reading the data
            line = saved_content[l][0]
            color = saved_content[l][1]
        else:
            for t in range(i, line_limit):
                textnodes[t].textnode.text = ""
                textnodes[t].char_interval = [0,0]
            return None
        
        text = [line[t:t+char_limit] for t in range(0,len(line),char_limit)]
        n = len(text)
        text.reverse()
        for j in range(n):
            if i < line_limit: 
                textnodes[i].textnode.text = text[j]
                textnodes[i].textnode.fg = color
                textnodes[i].line_index = len(saved_content) - l
                previous = ''
                for t in range(j): previous+=text[t]
                textnodes[i].char_interval = [len(previous), len(previous) + len(text[j])-1]
            i+=1
        l+=1
    return None


def displace(lines : list, char_limit : int, line_limit : int, textnodes : list, index : int, delta : int) -> int:
    """
    Displace all lines of a certain delta
    """
    # count defined lines
    n = len(textnodes)
    m = 0
    for x in lines:
        if not x==None:
            m += int(len(x)%char_limit != 0) + len(x)//char_limit + int(len(x) == 0) # count the defined lines (an undefined line would return None as line_index) 
    # initialize counter
    if delta == 1:
        if index + line_limit >= m: return index 
        i = 0
    elif delta == -1:
        if index <= 0: return index # reached the bottom
        i = n-1
    else:
        i = None # avoid unbound i

    while 0 <= i < n:
        if i+delta < 0 or i+delta >=n: # limit
            boolsign = delta > 0 # boolean equivalent of delta (delta equals +-1)
            if not textnodes[i].line_index == None:
                chunk = lines[textnodes[i].line_index][0]
                chunkcolor = lines[textnodes[i].line_index][1]
            else:
                chunk = ''
                chunkcolor = (1,1,1,1)
            # splitting and formatting process
            ci = textnodes[i].char_interval
            if boolsign and textnodes[i].line_index > 0: # going up
                if ci[0] == 0: # loading new line
                    offboundstr = lines[textnodes[i].line_index - delta][0]
                    offboundfg = lines[textnodes[i].line_index - delta][1]
                    temp = [offboundstr[t:t+char_limit] for t in range(0,len(offboundstr),char_limit)]
                    if len(temp) == 0: temp = [''] # avoid IndexError on temp[-1] call
                    textnodes[i].textnode.text = temp[-1]
                    textnodes[i].textnode.fg = offboundfg
                    textnodes[i].line_index = textnodes[i].line_index - delta
                    textnodes[i].char_interval = [len(offboundstr)-len(temp[-1]),len(offboundstr)-1]
                else: # keep loading the same line                    
                    textnodes[i].textnode.text = chunk[max(ci[0] - char_limit, 0) : ci[0]]
                    textnodes[i].char_interval = [max(ci[0] - char_limit, 0) , ci[0]]
                    textnodes[i].textnode.fg = chunkcolor
                    # line_index stays the same
            elif not(boolsign): # going down
                if ci[1] == len(chunk) - 1: # loading new line
                    offboundstr = lines[textnodes[i].line_index - delta][0] # delta is a relative int
                    offboundfg = lines[textnodes[i].line_index - delta][1]
                    
                    textnodes[i].textnode.text = offboundstr[:min(char_limit, len(offboundstr))]
                    textnodes[i].char_interval = [0,min(char_limit-1, len(offboundstr)-1)]
                    
                    textnodes[i].textnode.fg = offboundfg
                    textnodes[i].line_index = textnodes[i].line_index - delta
                else: # keep loading the same line
                    textnodes[i].textnode.text = chunk[ci[1]+1 : min(len(chunk),ci[1]+1+char_limit)]
                    textnodes[i].char_interval = [ci[1]+1 , min(len(chunk)-1,ci[1]+char_limit)]
                    textnodes[i].textnode.fg = chunkcolor
                    # line_index stays the same
        else: # middle lines (no need to load)
            textnodes[i].textnode.text = textnodes[i+delta].textnode.text
            textnodes[i].textnode.fg = textnodes[i+delta].textnode.fg
            textnodes[i].line_index = textnodes[i+delta].line_index
            textnodes[i].char_interval = textnodes[i+delta].char_interval
        i+=delta
    index += delta
    return index

def find_all_list(element, list): # unused
    indices = []
    for i in range(len(list)):
        if element == list[i]:
            indices.append(i)
    return indices