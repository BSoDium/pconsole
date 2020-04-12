try:
    from direct.gui.OnscreenImage import OnscreenImage
    from direct.gui.DirectGui import *
    from direct.gui.OnscreenText import OnscreenText
    from panda3d.core import *
    import importlib
    import pathlib
except ModuleNotFoundError:
    print('[Panda3d console]: Failed to import panda3d module')
import sys,os


temp = os.path.dirname(__file__)
MAINDIR = Filename.from_os_specific(str(pathlib.Path(temp).resolve())).getFullpath()


class Console:
    def __init__(self):
        base.a2dBottomLeft.set_bin('gui-popup', 0) # prevent overlapping issues
        return None
        
    def create(self, CommandDictionary, event:str = "f1"):
        self.CommandDictionary = {**CommandDictionary,**{"usage":self.helper,"help":self.showCommands}} # copy for further use in other methods
        self.hidden = False
        self.textscale = 0.04
        self.Lines = 47
        self.font = loader.loadFont(MAINDIR + '/TerminusTTF-4.47.0.ttf')
        self.background = OnscreenImage(image =MAINDIR + "/bg.png",pos = (0.65,0,1), parent = base.a2dBottomLeft)
        self.background.setTransparency(TransparencyAttrib.MAlpha)
        self.SavedLines = [OnscreenText(text = '', 
                                            pos = (0.01, 0.1 + x*self.textscale), 
                                            scale = self.textscale, 
                                            align = TextNode.ALeft, 
                                            fg = (1,1,1,1), 
                                            parent = base.a2dBottomLeft,
                                            font= self.font) for x in range(self.Lines)]
        self.loadConsoleEntry()
        self.commands = self.CommandDictionary
        self.callBackIndex = -1
        self.InputLines = []
        #self.entry.reparent_to(App)
        base.accept(event,self.toggle)
        base.accept('arrow_up',self.callBack,[True])
        base.accept('arrow_down',self.callBack,[False])

        self.ConsoleOutput('- Panda3d runtime console by Balrog -',color = Vec4(0,0,1,1))
        self.ConsoleOutput('successfully loaded all components',color = Vec4(0,1,0,1))
        self.toggle() # initialize as hidden
        return None
    
    def loadConsoleEntry(self): #-1.76, 0, -0.97
        self.entry = DirectEntry(scale=self.textscale,
                                    frameColor=(0,0,0,1),
                                    text_fg = (1,1,1,1),
                                    pos = (0.015, 0, 0.03),
                                    overflow = 1,
                                    command=self.ConvertToFunction,
                                    initialText="",
                                    numLines = 1,
                                    focus=True,
                                    width = 40,
                                    parent = base.a2dBottomLeft,
                                    entryFont = self.font)
        return None
    
    def toggle(self):
        if self.hidden:
            for i in self.SavedLines:
                i.show()
            self.entry.show()
            self.background.show()
            
        else:
            for i in self.SavedLines:
                i.hide()
            self.entry.hide()
            self.background.hide()
        self.hidden = not(self.hidden)
        return None
    
    def clearText(self):
        self.entry.enterText('')
        return None
    
    def ConvertToFunction(self,data):
        # callback stuff
        self.callBackIndex = -1
        self.InputLines.append(data)

        # gui
        self.entry.destroy()
        self.loadConsoleEntry()
        self.ConsoleOutput(" ")
        self.ConsoleOutput(str(MAINDIR)+"> "+data)

        Buffer = []
        ind = data.find('(')
        if ind <= 0: # no occurence
            Buffer.append(data)
        else:
            Buffer.append(data[0:ind]) # indentify keyword
            data = data[ind:len(data)] # strip the string as we move along
            if not(data[0] == '(' and data[len(data)-1] == ')'): # closing parenthesis syntax stuff
                self.ConsoleOutput('Missing parenthesis ")" in "'+ Buffer[0] + data + '"', (1,0,0,1))
                return None
            else:pass

            data = data[1:len(data)-1] # cut these useless '()' out

            left = find_all('(', data)
            right = find_all(')', data)
            if len(left) != len(right): # unmatched parethesis error
                self.ConsoleOutput('SyntaxError: unmatched parenthesis found in expression', (1,0,0,1))
                return None
            # we need to split the list according to the parenthesis structure 
            
            nl = len(left)
            for i in range(nl):
                temp = data[left[i]:right[i]+1].replace(',', '|') 
                temp = ' '+temp[1:len(temp)-1]+' ' # the spaces compensate the index gap
                data = data[:left[i]] + temp + data[right[i]+1:]

            Buffer += data.split(',') # identify arguments
            for i in range(len(Buffer)):
                Buffer[i] = Buffer[i].strip()
                if '|' in Buffer[i]:
                    Buffer[i] = Buffer[i].split('|') # internal tuples
                    for j in range(len(Buffer[i])):
                        Buffer[i][j] = Buffer[i][j].strip()     
            # now the string has been converted into a readable list

            for j in range(1, len(Buffer)):
                try:
                    if str(int(Buffer[j])) == Buffer[j]:
                        Buffer[j] = int(Buffer[j])
                except:
                    pass
                try:
                    if str(float(Buffer[j])) == Buffer[j]:
                        Buffer[j] = float(Buffer[j])
                except ValueError:
                    if str(Buffer[j]) != 'None':
                        Buffer[j] = str(Buffer[j])
                    else:
                        Buffer[j] = None
                except TypeError:
                    if type(Buffer[j]) is list:
                        for t in range(len(Buffer[j])): # a recursive algorithm might have been a better option
                            try:
                                if str(int(Buffer[j][t])) == Buffer[j][t]:
                                    Buffer[j][t] = int(Buffer[j][t])
                            except ValueError:
                                pass
                            try:
                                if str(float(Buffer[j][t])) == Buffer[j][t]:
                                    Buffer[j][t] = float(Buffer[j][t])
                            except ValueError:
                                if str(Buffer[j][t]) != 'None':
                                    Buffer[j][t] = str(Buffer[j][t])
                                else:
                                    Buffer[j][t] = None
                        Buffer[j] = tuple(Buffer[j])

                # formating is done, let's head over to the execution
        
        try:
            ChosenCommand = self.commands[Buffer[0]]
            if len(Buffer)-1 and Buffer[1] != '': # several arguments have been provided
                try:
                    ChosenCommand(*Buffer[1:])
                    return None
                except TypeError:
                    self.ConsoleOutput("Wrong arguments provided", (1,0,0,1))
                    return None
            else:
                try:
                    ChosenCommand()
                    return None
                except TypeError:
                    self.ConsoleOutput('This command requires (at least) one argument', (1,0,0,1))
                    return None
        except:
            self.CommandError(Buffer[0])
        return None
        

    def SError(self,report):
        self.ConsoleOutput("Traceback (most recent call last):", (1,0,0,1))
        self.ConsoleOutput("Incorrect use of the '"+str(report)+"' command", (1,0,0,1))
        return None
    
    def CommandError(self,report):
        self.ConsoleOutput("Traceback (most recent call last):", (1,0,0,1))
        self.ConsoleOutput("SyntaxError: command '"+str(report)+"' is not defined", (1,0,0,1))
    
    def ConsoleOutput(self,output, color:Vec4 = Vec4(1,1,1,1), mode:str = 'add'):
        #maxsize = self.entry['width']
        
        maxsize = 81
        #maxsize = 66 # hermit font
        discretized = [output[i:i+maxsize] for i in range(0,len(output),maxsize)]
        if mode == 'add':
            for i in discretized: # for each line
                for x in range(self.Lines-1,0,-1):
                    self.SavedLines[x].text = self.SavedLines[x-1].text
                    self.SavedLines[x].fg = self.SavedLines[x-1].fg
                self.SavedLines[0].text = i
                self.SavedLines[0].fg = color
        elif mode == 'edit':
            n = len(discretized)
            for i in range(n):
                self.SavedLines[i].text = discretized[n - i - 1]
                self.SavedLines[i].fg = color
        return None
    
    def helper(self,index):
        '''
        Provides help concerning a given command
        '''
        try:
            i = self.CommandDictionary[index]
            self.ConsoleOutput("Help concerning command '%s':" % str(index), color = (0.243,0.941,1,1))
            self.ConsoleOutput("- associated function name is '%s'" % str(i.__name__))
            self.ConsoleOutput("- Documentation provided: ")
            doc = self.TextToLine(str(i.__doc__))
            if not doc == str(None):
                self.ConsoleOutput(doc.strip())
            else:
                self.ConsoleOutput("No docstring found")
            self.ConsoleOutput("- Known arguments: ")
            
            arg = list(i.__code__.co_varnames)
            del arg[0] # remove the self argument
            arg = str(arg)
            if len(arg)-2:
                self.ConsoleOutput(str(arg)[1:len(str(arg))-1]) # remove brackets
            else:
                self.ConsoleOutput("No arguments required")
        except KeyError:
            self.ConsoleOutput("Unknown command '%s'" % str(index), (1,0,0,1))
        return None
    
    def showCommands(self):
        '''
        Shows a list of available commands
        '''
        self.ConsoleOutput("List of available commands: ", color = (0.243,0.941,1,1))
        for i in self.CommandDictionary:
            self.ConsoleOutput("- "+str(i))
        self.ConsoleOutput(" ")
        self.ConsoleOutput("Use usage(command) for more details on a specific command")
        return None

    def callBack(self, key : bool):
        invertedInput = self.InputLines[::-1]
        if key: # up key pressed
            try: # avoid out of range errors
                if self.callBackIndex < len(invertedInput):
                    self.callBackIndex += 1
                    self.entry.enterText(invertedInput[self.callBackIndex])
            except: pass
        else:
            try:
                if self.callBackIndex >= 0:
                    self.callBackIndex -= 1
                    self.entry.enterText(([''] + invertedInput)[self.callBackIndex])
            except: pass
        
    def TextToLine(self,text):
        try:
            text = text.replace("\n","")
        except:
            pass
        return text

def find_all(sample, string):
    n = len(sample)
    poslist = []
    for i in range(len(string)-n+1):
        if string[i:i+n] == sample:
            poslist.append(i)
        else:pass
    return poslist