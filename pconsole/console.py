# -*- coding: utf-8 -*-

try:
    from direct.gui.OnscreenImage import OnscreenImage
    from direct.gui.DirectGui import *
    from direct.gui.OnscreenText import OnscreenText
    from panda3d.core import *
    import panda3d
except ModuleNotFoundError:
    print('[Panda3d console]: Failed to import panda3d module')
import sys,os, __main__, traceback, importlib, pathlib
from .version import __version__ as version
from .file import BufferFile
from code import InteractiveInterpreter

temp = os.path.dirname(__file__)
PYMAINDIR = str(pathlib.Path(temp).resolve())
MAINDIR = Filename.from_os_specific(PYMAINDIR).getFullpath()

class Console:
    def __init__(self):
        base.a2dBottomLeft.set_bin('gui-popup', 0) # prevent overlapping issues
        sys.stdout = BufferFile(self.ConsoleOutput)
        sys.stderr = BufferFile(self.CMDError)
        return None
        
    def create(self, CommandDictionary, event:str = "f1", app = None):
        defaults = {"usage":self.usage,
                    "help":self.help,
                    "credits":self.credits,
                    "license":self.showLicense}
        self.CommandDictionary = {**CommandDictionary,**defaults} # copy for further use in other methods
        self.consoles = [
            "csl> ",
            " py> ",
            "cmd> "
        ]
        self.hidden = False
        self.textscale = 0.04
        self.Lines = 47
        self.font = loader.loadFont(MAINDIR + '/TerminusTTF-4.47.0.ttf')
        self.background = OnscreenImage(image =MAINDIR + "/bg.png", pos = (0.65,0,1), parent = base.a2dBottomLeft, color = (1,1,1,0.95))
        self.background.setTransparency(TransparencyAttrib.MAlpha)
        self.SavedLines = [OnscreenText(text = '', 
                                            pos = (0.01, 0.1 + x*self.textscale), 
                                            scale = self.textscale, 
                                            align = TextNode.ALeft, 
                                            fg = (1,1,1,1), 
                                            parent = base.a2dBottomLeft,
                                            font= self.font) for x in range(self.Lines)]
        self.indicator = DirectButton(text = 'csl> ', command = self.switch_adr, scale = self.textscale, frameColor = (0,0,0,0), text_font = self.font, pressEffect = False, pos = (0.01, 0, 0.031), text_fg = (1,1,1,1), text_align = TextNode.ALeft, parent = base.a2dBottomLeft)
        self.loadConsoleEntry()
        self.commands = self.CommandDictionary
        self.callBackIndex = -1
        self.InputLines = []
        #self.entry.reparent_to(App)
        base.accept(event,self.toggle)
        base.accept('arrow_up',self.callBack,[True])
        base.accept('arrow_down',self.callBack,[False])

        self.ConsoleOutput('Pconsole ' + version,color = Vec4(0,0,1,1))
        self.ConsoleOutput('Successfully loaded all components',color = Vec4(0,1,0,1))
        self.ConsoleOutput('Type "help", "credits" or "license" for more information.')
        self.app = app
        if self.app == None: 
            self.ConsoleOutput("Warning: 'main' keyword is not available in the python shell, as the 'app' \nargument was not provided")
        self.toggle() # initialize as hidden
        return None
    
    def loadConsoleEntry(self): #-1.76, 0, -0.97
        self.entry = DirectEntry(scale=self.textscale,
                                    frameColor = (0.05,0.05,0.05,0),
                                    text_fg = (1,1,1,1),
                                    pos = (0.1, 0, 0.03),
                                    overflow = 1,
                                    command=self.ConvertToFunction,
                                    initialText="",
                                    numLines = 1,
                                    focus=True,
                                    width = 38,
                                    parent = base.a2dBottomLeft,
                                    entryFont = self.font)
        return None
    
    def toggle(self):
        if self.hidden:
            for i in self.SavedLines:
                i.show()
            self.entry.show()
            self.background.show()
            self.indicator.show()
            
        else:
            for i in self.SavedLines:
                i.hide()
            self.entry.hide()
            self.background.hide()
            self.indicator.hide()
        self.hidden = not(self.hidden)
        return None
    
    def clearText(self):
        self.entry.enterText('')
        return None
    
    def ConvertToFunction(self,data):

        if len(data) == 0: return None 
        # callback stuff
        self.callBackIndex = -1
        self.InputLines.append(data)

        # gui
        self.entry.destroy()
        self.loadConsoleEntry()
        self.ConsoleOutput(" ")
        self.ConsoleOutput(str(MAINDIR)+"> "+data)

        # cmd debugger check
        if self.indicator['text'] == ' py> ':
            main = self.app
            try:
                exec(data.strip())
            except Exception:
                self.CMDError(traceback.format_exc())
            return None
        # common command
        elif self.indicator['text'] == 'csl> ':
            ind = data.find('(')
            Buffer = []
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
        elif self.indicator['text'] == 'cmd> ':
            '''
            try:
                self.CMDprocess = os.system(data.strip())
            except:
                self.CMDError(traceback.format_exc())
            '''
            self.CMDError('Sorry, this console has been temporarily disabled.')
        return None
        

    def CMDError(self,report):
        sys.__stderr__.write(report)
        self.ConsoleOutput(report, (1,0,0,1))
        return None
    
    def CommandError(self,report):
        self.ConsoleOutput("Traceback (most recent call last):", (1,0,0,1))
        self.ConsoleOutput("SyntaxError: command '"+str(report)+"' is not defined", (1,0,0,1))
    
    def ConsoleOutput(self,output, color:Vec4 = Vec4(1,1,1,1), mode:str = 'add', CMD_type = False):
        if CMD_type: sys.__stdout__.write(output)
        #maxsize = self.entry['width']
        maxsize = 81
        #maxsize = 66 # hermit font
        text = output.split('\n')
        text = [[x[i:i+maxsize] for i in range(0,len(x),maxsize)] for x in text]
        if mode == 'add':
            for discretized in text:
                for i in discretized: # for each line
                    for x in range(self.Lines-1,0,-1):
                        self.SavedLines[x].text = self.SavedLines[x-1].text
                        self.SavedLines[x].fg = self.SavedLines[x-1].fg
                    self.SavedLines[0].text = i
                    self.SavedLines[0].fg = color
        elif mode == 'edit':
            for discretized in text:
                n = len(discretized)
                for i in range(n):
                    self.SavedLines[i].text = discretized[n - i - 1]
                    self.SavedLines[i].fg = color
        return None
    
    def switch_adr(self):
        current = self.indicator['text']
        n = self.consoles.index(current)
        if n == len(self.consoles)-1:
            n = 0
        else:
            n+=1
        self.indicator['text'] = self.consoles[n]
    def usage(self,index):
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
            #del arg[0] # remove the self argument
            arg = str(arg)
            if len(arg)-2:
                self.ConsoleOutput(str(arg)[1:len(str(arg))-1]) # remove brackets
            else:
                self.ConsoleOutput("No arguments required")
        except KeyError: # not in the dictionary
            self.ConsoleOutput("Unknown command '%s'" % str(index), (1,0,0,1))
        return None
    
    def help(self):
        '''
        Shows a list of available commands
        '''
        self.ConsoleOutput("List of available commands: ", color = (0.243,0.941,1,1))
        for i in self.CommandDictionary:
            self.ConsoleOutput("- "+str(i))
        self.ConsoleOutput(" ")
        self.ConsoleOutput("Use usage(command) for more details on a specific command")
        return None

    def credits(self):
        self.ConsoleOutput("Thanks to rdb, darthrigg, and the panda3d community for supporting this project")
        self.ConsoleOutput("This program was created by l3alr0g. See https://github.com/l3alr0g/pconsole for more information")
        self.ConsoleOutput("Download the panda3d engine at panda3d.org")

    def showLicense(self):
        with open(PYMAINDIR + '\license.txt') as l:
            license = l.read()
        self.ConsoleOutput(license, color = (1, 0.9, 0.7, 1))

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