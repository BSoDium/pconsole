# -*- coding: utf-8 -*-

try:
    from direct.gui.OnscreenImage import OnscreenImage
    from direct.gui.DirectGui import *
    from direct.gui.OnscreenText import OnscreenText
    from direct.showbase.ShowBase import DirectObject
    from panda3d.core import *
    import panda3d
except ModuleNotFoundError:
    print('[Panda3d console]: Failed to import panda3d module')
import sys, os, traceback, importlib, pathlib, json, subprocess, threading
from .cmd_command import Command
from .version import __version__ as version
from .file import BufferFile
from .lines import redistribute, displace, OnscreenLine
from .defaults import __blacklist__ # change to module names when defined

temp = os.path.dirname(__file__)
PYMAINDIR = str(pathlib.Path(temp).resolve())
MAINDIR = Filename.from_os_specific(PYMAINDIR).getFullpath()


class Console:
    def __init__(self):
        base.a2dBottomLeft.set_bin('gui-popup', 0) # prevent overlapping issues
        sys.stdout = BufferFile(self.ConsoleOutput)
        sys.stderr = BufferFile(self.CMDError)
        self.res = (base.win.getXSize(), base.win.getYSize(), base.getAspectRatio())
        return None
        
    def create(self, CommandDictionary, event:str = "f1", app = None):
        # dictionnaries and commands
        defaults = {"usage":self.usage,
                    "help":self.help,
                    "credits":self.credits,
                    "license":self.showLicense}
        self.CommandDictionary = {**CommandDictionary,**defaults} # copy for further use in other methods
        self.consoles = {
            "csl> ":"Pconsole "+version,
            "pyt> ":sys.version[:5]+" runtime python console",
            "cmd> ":"Microsoft windows commandline"
        }
        
        # settings 
        with open(PYMAINDIR + '\config.json') as config:
            data = json.load(config)
        self._verbose = data['toggleverbose']
        self._framesize = data['framesize'] # [2 , 2] for fullscreen
        self._disponstartup = data['disponstartup']
        self._minframesize = [0.8, 1]
        self._check_version = data['checkforupdates']
        if self._framesize[0] < self._minframesize[0] or self._framesize[1] < self._minframesize[1]:
            self._framesize = self._minframesize
        self._Resframesize = [self._framesize[0]*self.res[2], self._framesize[1]] # modified framesize according to screen res (most screens aren't square)
        self.hidden = False
        self._textscale = data['textscale']
        self._textres = data['textres']
        self._doresizeroutine = data['doresizeroutine']
        self._doscrollingroutine = data['doscrollingroutine']
        self._font = loader.loadFont(MAINDIR + data['fontpath'])
        self._font.setPixelsPerUnit(self._textres)
        self._callBackIndex = -1
        self._scrollingIndex = 0 # start in non-scrolled state
        self._InputLines = []
        self._SavedLines = [] # this list will contain the recorded lines (for scrolling and resizing purpose)
        # resizing
        self.recomputeFrame()
        
        # gui objects
        self._gui = NodePath('GuiNp')
        self._gui.reparentTo(base.a2dBottomLeft)
        _cardmaker = CardMaker('bg')
        _cardmaker.setFrame(-0, self._framesize[0], 0, self._framesize[1])
        _cardmaker.setColor(0,0,0,0.95)
        _cardmaker.set_has_uvs(False)
        _cardmaker.set_has_normals(False)
        self._background = self._gui.attach_new_node(_cardmaker.generate())
        self._background.setTransparency(TransparencyAttrib.MAlpha)\
        #instead of creating the background using the current resolution, we use scaling to adapt its size whenever the user changes the window's size
        self._background.setScale(self._Resframesize[1]/self._framesize[1], 1, self._Resframesize[0]/self._framesize[0])
        
        self._LinesOnDisplay = [OnscreenLine(text = '', 
                                            pos = (0.01, 0.12 + x*self._textscale), 
                                            scale = self._textscale, 
                                            align = TextNode.ALeft, 
                                            fg = (1,1,1,1), 
                                            parent = self._gui,
                                            font= self._font,
                                            line = None) for x in range(self._maxlines)] # the 0 value is the index of the chunk (the actual line)
        self._indicator = DirectButton(text = 'csl> ', 
                                      command = self.switch_adr, 
                                      scale = self._textscale, 
                                      pos = (0.01, 0, 0.049), 
                                      frameColor = (0,0,0,0), 
                                      text_font = self._font, 
                                      pressEffect = False, 
                                      text_fg = (1,1,1,1), 
                                      text_align = TextNode.ALeft, 
                                      parent = self._gui)
        self._info = OnscreenText(text = 'targeting: 3.8.3 runtime python console ', 
                                pos = (0.01, 0.01), 
                                scale = self._textscale*0.95, 
                                align = TextNode.ALeft, 
                                fg = (0.7,0.9,0.9,1), 
                                parent = self._gui,
                                font= self._font)
        self.loadConsoleEntry()
        self.update_res()

        # head
        self.ConsoleOutput('Pconsole ' + version,color = Vec4(0.1,0.1,1,1))
        self.ConsoleOutput('Successfully loaded all components',color = Vec4(0,1,0,1))
        self.ConsoleOutput('Type "help", "credits" or "license" for more information.')
        self.ConsoleOutput("Click the prompt keyword or press f2 to change the targeted console")

        # check for updates in a separate thread
        thread = threading.Thread(target = self.versioncheck, args = ())
        thread.daemon = True
        thread.start()

        # base.buttonThrowers
        self._eventhandler = DirectObject.DirectObject()
        if event == 'f2':
            self.ConsoleOutput('failed to configure %s key as toggling event, loading default (f1)' %event, Vec4(0.8,0.8,1,1))
            event = 'f1' # default if conflict with f2
        self._eventhandler.accept(event , self.toggle)
        self._eventhandler.accept('arrow_up',self.callBack,[True])
        self._eventhandler.accept('arrow_down',self.callBack,[False])
        self._eventhandler.accept('f2', self.switch_adr)
        if self._doscrollingroutine:
            self._eventhandler.accept('wheel_up', self.scroll, [True])
            self._eventhandler.accept('wheel_down', self.scroll, [False])
        if self._doresizeroutine: self._eventhandler.accept('aspectRatioChanged', self.update_res)

        self.app = app
        if self.app == None: 
            self.ConsoleOutput("Warning: 'main' keyword is not available in the python shell, as the 'app' \nargument was not provided")
        if not self._disponstartup: self.toggle() # initialize as hidden
        return None
    
    def loadConsoleEntry(self): #-1.76, 0, -0.97
        self.entry = DirectEntry(scale=self._textscale,
                                    frameColor = (0.05,0.05,0.05,0),
                                    text_fg = (1,1,1,1),
                                    pos = (0.1, 0, 0.05),
                                    overflow = 1,
                                    command=self.ConvertToFunction,
                                    initialText="",
                                    numLines = 1,
                                    focus=True,
                                    width = 38,
                                    parent = self._gui,
                                    entryFont = self._font)
        return None
    
    def toggle(self):
        if self.hidden:
            self._gui.show()
        else:
            self._gui.hide()
        self.hidden = not(self.hidden)
        return None
    
    def clearText(self):
        self.entry.enterText('')
        return None
    
    def ConvertToFunction(self,data):

        if len(data) == 0: return None 
        # callback stuff
        self._callBackIndex = -1
        self._InputLines.append(data)

        # gui
        self.entry.destroy()
        self.loadConsoleEntry()
        self.ConsoleOutput(" ")
        self.ConsoleOutput(self._indicator['text']+data)

        def pyt_process():
            nonlocal data, self
            main = self.app
            data = data.strip()
            forb = list(__blacklist__.keys())
            for a in forb:
                k = len(a)
                if data[:k] == a:
                    self.CMDError('Sorry, this command has been disabled internally\nReason:')
                    self.CMDError(__blacklist__[a])
                    return None
            try:
                exec(data.strip())
            except Exception:
                self.CMDError(traceback.format_exc())
            except SystemExit:
                pass
            return None
        
        def csl_process():
            nonlocal data, self
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

                left = find_all_str('(', data)
                right = find_all_str(')', data)
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
                ChosenCommand = self.CommandDictionary[Buffer[0]]
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
            
        def cmd_process():
            nonlocal data, self
            command = Command(data.strip())
            try:
                code, output = command.run(timeout = 1)
                self.ConsoleOutput(output[0])
                self.CMDError(output[1])
            except:
                self.CMDError(traceback.format_exc())
            
        if self._indicator['text'] == 'pyt> ':
            pyt_process()
        elif self._indicator['text'] == 'csl> ':
            csl_process()
        elif self._indicator['text'] == 'cmd> ':
            cmd_process()
        return None
        

    def CMDError(self,report):
        if report == None: return
        elif type(report) is not str: report = str(report)
        else:
            sys.__stderr__.write(report)
            self.ConsoleOutput(report, (1,0,0,1))
        return 
    
    def CommandError(self,report):
        self.ConsoleOutput("Traceback (most recent call last):", (1,0,0,1))
        self.ConsoleOutput("SyntaxError: command '"+str(report)+"' is not defined", (1,0,0,1))
    
    def ConsoleOutput(self, output, color:Vec4 = Vec4(1,1,1,1), mode:str = 'add', CMD_type = False):
        keywords = {'cmd> ':'\\r\\n', 'pyt> ':'\n', 'csl> ':'\n'}
        if output == None: return
        elif type(output) is not str: output = str(output)
        if CMD_type: sys.__stdout__.write(output)

        if self._indicator['text'] == 'cmd> ':
            text = output.split(keywords['cmd> '])
        elif self._indicator['text'] == 'pyt> ':
            text = output.split(keywords['pyt> '])
        elif self._indicator['text'] == 'csl> ':
            text = output.split(keywords['csl> '])
        
        text = [[x[i:i+self._maxsize] for i in range(0,len(x),self._maxsize)] for x in text]
        if mode == 'add':
            for discretized in text:
                self._SavedLines.append((''.join(discretized), color))
                for i in range(len(discretized)): # for each line
                    for x in range(self._maxlines-1,0,-1):
                        self._LinesOnDisplay[x].textnode.text = self._LinesOnDisplay[x-1].textnode.text
                        self._LinesOnDisplay[x].textnode.fg = self._LinesOnDisplay[x-1].textnode.fg
                        self._LinesOnDisplay[x].lineIndex = self._LinesOnDisplay[x-1].lineIndex
                        self._LinesOnDisplay[x].charInterval = self._LinesOnDisplay[x-1].charInterval
                    self._LinesOnDisplay[0].textnode.text = discretized[i]
                    self._LinesOnDisplay[0].textnode.fg = color
                    self._LinesOnDisplay[0].lineIndex = len(self._SavedLines)-1 # save the line number
                    previous = ''
                    for t in range(i): previous+=discretized[t] # sum up all the previous chars
                    self._LinesOnDisplay[0].charInterval = [len(previous), len(previous)+len(discretized[i])-1]
        elif mode == 'edit':
            self._SavedLines[-1] = (output, color) # save the line, might not work properly
            for discretized in text:
                n = len(discretized)
                for i in range(n):
                    self._LinesOnDisplay[i].textnode.text = discretized[n - i - 1]
                    self._LinesOnDisplay[i].textnode.fg = color
                    self._LinesOnDisplay[i].lineIndex = len(self._SavedLines)-1 # charinterval not handled
        return None
    
    def scroll(self, direction:bool):
        sign = (-1)**int(direction+1) # -1 or 1 depending on the boolean
        self._scrollingIndex = displace(self._SavedLines, self._maxsize, self._maxlines, self._LinesOnDisplay, self._scrollingIndex, sign)

    
    def switch_adr(self):
        current = self._indicator['text']
        n = list(self.consoles.keys()).index(current)
        if n == len(self.consoles.keys())-1:
            n = 0
        else:
            n+=1
        self._indicator['text'] = list(self.consoles.keys())[n]
        self._info.text = "targeting: " + self.consoles[self._indicator['text']]
    
    def update_res(self):
        self.res = (base.win.getXSize(), base.win.getYSize(), base.getAspectRatio()) # update res
        # update frame stuff
        self._Resframesize = [self._framesize[0]*self.res[2], self._framesize[1]]
        self.recomputeFrame()
        self._background.setScale(self._Resframesize[0]/self._framesize[0], 1, self._Resframesize[1]/self._framesize[1])
        # update text disposition
        redistribute(self._SavedLines, self._maxsize, self._maxlines, self._LinesOnDisplay)
        # debug
        if self._verbose: print('updated res to %s - x,y,ratio' %str((base.win.getXSize(), base.win.getYSize(), base.getAspectRatio())))

    def callBack(self, key : bool):
        invertedInput = self._InputLines[::-1]
        if key: # up key pressed
            try: # avoid out of range errors
                if self._callBackIndex < len(invertedInput):
                    self._callBackIndex += 1
                    self.entry.enterText(invertedInput[self._callBackIndex])
            except: pass
        else:
            try:
                if self._callBackIndex >= 0:
                    self._callBackIndex -= 1
                    self.entry.enterText(([''] + invertedInput)[self._callBackIndex])
            except: pass
        
    def textToLine(self,text):
        try:
            text = text.replace("\n","")
        except:
            pass
        return text

    def recomputeFrame(self):
        def getfontbounds():
            nonlocal self
            temp = OnscreenText(text = '1234567890', scale = self._textscale)
            bounds = temp.getTightBounds()
            temp.destroy()
            return bounds
        bounds = getfontbounds()
        width = (bounds[1][0] - bounds[0][0])/10
        self._maxsize = int(self._Resframesize[0]/width)
        self._maxlines = int((self._Resframesize[1]-0.12)/self._textscale) + 1

    def versioncheck(self):
        # version_check
        if not self._check_version: return
        self.ConsoleOutput(" \nChecking for updates...", Vec4(0.8,0.7,0,1))
        try:
            data = str(subprocess.run([sys.executable, '-m', 'pip', 'install', '{}==invalid'.format('pconsole')], capture_output=True, text=True)).split('from versions: ')[1]
            latest = data[:data.find(')')][-5:]
            if latest != version and int(''.join(version.split('.'))) < int(''.join(latest.split('.'))):
                self.ConsoleOutput("This version of pconsole ({}) is outdated.\nPlease consider updating it using the command 'pip install pconsole'\n ".format(version), Vec4(0.8,0.7,0,1))
            elif int(''.join(version.split('.'))) > int(''.join(latest.split('.'))):
                self.ConsoleOutput("This version of pconsole ({}) hasn't been released yet.\nIt may therefore contain some bugs.\nPlease consider installing a stable build using \n'pip install pconsole'\n ".format(version), Vec4(0.8,0.7,0,1))
            else:
                self.ConsoleOutput("This version of pconsole is currently up-to-date", Vec4(0.8,0.7,0,1))
        except:
            self.ConsoleOutput("failed to connect to the Pypi database\n ", Vec4(0.8,0.7,0,1))
        
    def usage(self,index):
        '''
        Provides help concerning a given command
        '''
        try:
            i = self.CommandDictionary[index]
            self.ConsoleOutput("Help concerning command '%s':" % str(index), color = (0.243,0.941,1,1))
            self.ConsoleOutput("- associated function name is '%s'" % str(i.__name__))
            self.ConsoleOutput("- Documentation provided: ")
            doc = self.textToLine(str(i.__doc__))
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
        self.ConsoleOutput("Thanks to rdb, darthrigg, and the panda3d community for supporting this project.")
        self.ConsoleOutput("This program was created by l3alr0g. See https://github.com/l3alr0g/pconsole for more information.")
        self.ConsoleOutput("Download the panda3d engine at panda3d.org")

    def showLicense(self):
        with open(PYMAINDIR + '\license.txt') as l:
            license = l.read()
        self.ConsoleOutput(license, color = (1, 0.9, 0.7, 1))

def find_all_str(sample, string):
    n = len(sample)
    poslist = []
    for i in range(len(string)-n+1):
        if string[i:i+n] == sample:
            poslist.append(i)
        else:pass
    return poslist
