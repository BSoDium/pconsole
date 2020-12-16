# -*- coding: utf-8 -*-

try:
    from direct.gui.OnscreenImage import OnscreenImage
    from direct.gui.DirectGui import *
    from direct.gui.OnscreenText import OnscreenText
    from direct.showbase.ShowBase import DirectObject, ShowBase
    from panda3d.core import Filename, NodePath, CardMaker, TransparencyAttrib, TextNode, Vec4
    import panda3d
except ModuleNotFoundError:
    print('[Panda3d console]: Failed to import panda3d module')
import sys
import os
import traceback
import importlib
import pathlib
import json
import subprocess
import threading
import requests
from .cmd_command import Command
from .version import __version__ as version
from .file import BufferFile
from .lines import redistribute, displace, OnscreenLine
from .win_convert import convert
from .defaults import __blacklist__  # change to module names when defined

temp = os.path.dirname(__file__)
PYMAINDIR = str(pathlib.Path(temp).resolve())
MAINDIR = Filename.from_os_specific(PYMAINDIR).getFullpath()  


class Console:
    def __init__(self):
        # prevent overlapping issues
        base.a2dBottomLeft.set_bin('gui-popup', 0)
        sys.stdout = BufferFile(self._ConsoleOutput)
        sys.stderr = BufferFile(self._CMDError)
        self.res = (base.win.getXSize(), base.win.getYSize(),
                    base.getAspectRatio())
        return None

    def create(self, CommandDictionary, event: str = "f1", app=None):
        # dictionnaries and commands
        defaults = {"usage": self.usage,
                    "help": self.help,
                    "credits": self.credits,
                    "license": self.showLicense}
        # copy for further use in other methods
        self.CommandDictionary = {**CommandDictionary, **defaults}
        self.consoles = {
            "csl> ": "Pconsole " + version,
            "pyt> ": sys.version[:5]+" runtime python console",
            "cmd> ": "OS commandline"
        }

        # settings
        with open(os.path.join(PYMAINDIR, 'win_symbols.json'), encoding='utf-8') as w_symb:
            self.win_symbols = json.load(w_symb)
        with open(os.path.join(PYMAINDIR, 'config.json')) as config:
            data = json.load(config)
        self._verbose = data['toggleverbose']
        self._bg_transp = data['bg_transparency']
        self._framesize = data['framesize']  # [2 , 2] for fullscreen
        self._disponstartup = data['disponstartup']
        self._minframesize = [0.8, 1]
        self._check_version = data['checkforupdates']
        if self._framesize[0] < self._minframesize[0] or self._framesize[1] < self._minframesize[1]:
            self._framesize = self._minframesize
        # modified framesize according to screen res (most screens aren't square)
        self._Resframesize = [self._framesize[0]
            * self.res[2], self._framesize[1]]
        self.hidden = False
        self._textscale = data['textscale']
        self._textres = data['textres']
        self._doresizeroutine = data['doresizeroutine']
        self._doscrollingroutine = data['doscrollingroutine']
        self._font = loader.loadFont(os.path.join(MAINDIR, data['fontpath']))
        self._font.setPixelsPerUnit(self._textres)
        self._callBackIndex = -1
        self._scrollingIndex = 0  # start in non-scrolled state
        self._InputLines = []
        # this list will contain the recorded lines (for scrolling and resizing purpose)
        self._SavedLines = []
        # resizing
        self._recomputeFrame()

        # gui objects
        self._gui = NodePath('GuiNp')
        self._gui.reparentTo(base.a2dBottomLeft)
        _cardmaker = CardMaker('bg')
        _cardmaker.setFrame(-0, self._framesize[0], 0, self._framesize[1])
        _cardmaker.setColor(0, 0, 0, self._bg_transp)
        _cardmaker.set_has_uvs(False)
        _cardmaker.set_has_normals(False)
        self._background = self._gui.attach_new_node(_cardmaker.generate())
        self._background.setTransparency(TransparencyAttrib.MAlpha)\
        # instead of creating the background using the current resolution, we use scaling to adapt its size whenever the user changes the window's size
        self._background.setScale(
            self._Resframesize[1]/self._framesize[1], 1, self._Resframesize[0]/self._framesize[0])

        self._LinesOnDisplay = [OnscreenLine(text='',
                                            pos=(0.01, 0.12 + x *
                                                 self._textscale),
                                            scale=self._textscale,
                                            align=TextNode.ALeft,
                                            fg=(1, 1, 1, 1),
                                            parent=self._gui,
                                            font=self._font,
                                            line=None) for x in range(self._maxlines)]  # the 0 value is the index of the chunk (the actual line)
        self._indicator = DirectButton(text='csl> ',
                                      command=self._switch_adr,
                                      scale=self._textscale,
                                      pos=(0.01, 0, 0.049),
                                      frameColor=(0, 0, 0, 0),
                                      text_font=self._font,
                                      pressEffect=False,
                                      text_fg=(1, 1, 1, 1),
                                      text_align=TextNode.ALeft,
                                      parent=self._gui)
        self._info = OnscreenText(text='targeting: ' + self.consoles[self._indicator['text']],
                                pos=(0.01, 0.01),
                                scale=self._textscale*0.95,
                                align=TextNode.ALeft,
                                fg=(0.7, 0.9, 0.9, 1),
                                parent=self._gui,
                                font=self._font)
        self._loadConsoleEntry()
        self._update_res()

        # head
        self._ConsoleOutput('Pconsole ' + version, color=Vec4(0.1, 0.1, 1, 1))
        self._ConsoleOutput(
            'Successfully loaded all components', color=Vec4(0, 1, 0, 1))
        self._ConsoleOutput(
            'Type "help", "credits" or "license" for more information.')
        self._ConsoleOutput(
            "Click the prompt keyword or press f2 to change the targeted console")

        # base.buttonThrowers
        self._eventhandler = DirectObject.DirectObject()
        if event == 'f2':
            self._ConsoleOutput(" ")
            self._ConsoleOutput(
                'failed to configure %s key as toggling event, loading default (f1)' % event, Vec4(0.8, 0.8, 1, 1))
            event = 'f1'  # default if conflict with f2
        self._eventhandler.accept(event, self._toggle)
        self._eventhandler.accept('arrow_up', self._callBack, [True])
        self._eventhandler.accept('arrow_down', self._callBack, [False])
        self._eventhandler.accept('f2', self._switch_adr)
        if self._doscrollingroutine:
            self._eventhandler.accept('wheel_up', self._scroll, [True])
            self._eventhandler.accept('wheel_down', self._scroll, [False])
        if self._doresizeroutine: self._eventhandler.accept(
            'aspectRatioChanged', self._update_res)

        self.app = app
        if self.app == None:
            self._ConsoleOutput(" ")
            self._ConsoleOutput(
                "Warning: 'main' keyword is not available in the python shell, as the 'app' \nargument was not provided")
        if not self._disponstartup: self._toggle()  # initialize as hidden

        # check for updates in a separate thread
        thread = threading.Thread(target=self._versioncheck, args=())
        thread.daemon = True
        thread.start()

        return None

    def _loadConsoleEntry(self):  # -1.76, 0, -0.97
        self.entry = DirectEntry(scale=self._textscale,
                                    frameColor=(0.05, 0.05, 0.05, 0),
                                    text_fg=(1, 1, 1, 1),
                                    pos=(0.1, 0, 0.05),
                                    overflow=1,
                                    command=self._ConvertToFunction,
                                    initialText="",
                                    numLines=1,
                                    focus=True,
                                    width=38,
                                    parent=self._gui,
                                    entryFont=self._font)
        return None

    def _toggle(self):
        if self.hidden:
            self._gui.show()
        else:
            self._gui.hide()
        self.hidden = not(self.hidden)
        return None

    def _ConvertToFunction(self, data):

        if len(data) == 0: return None
        # callback stuff
        self._callBackIndex = -1
        self._InputLines.append(data)

        # gui
        self.entry.destroy()
        self._loadConsoleEntry()
        self._ConsoleOutput(" ")
        self._ConsoleOutput(self._indicator['text']+data)

        def pyt_process():
            nonlocal data, self
            main = self.app  # defined so the user can access it from the commandline
            data = data.strip()
            forb = list(__blacklist__.keys())
            for a in forb:
                k = len(a)
                if data[:k] == a:
                    self._CMDError(
                        'Sorry, this command has been disabled internally\nReason:')
                    self._CMDError(__blacklist__[a])
                    return None
            try:
                exec(data.strip())
            except Exception:
                self._CMDError(traceback.format_exc())
            except SystemExit:
                pass
            return None

        def csl_process():
            nonlocal data, self
            ind = data.find('(')
            Buffer = []
            if ind <= 0:  # no occurence
                Buffer.append(data)
            else:
                Buffer.append(data[0:ind])  # indentify keyword
                data = data[ind:len(data)]  # strip the string as we move along
                # closing parenthesis syntax stuff
                if not(data[0] == '(' and data[len(data)-1] == ')'):
                    self._ConsoleOutput(
                        'Missing parenthesis ")" in "' + Buffer[0] + data + '"', (1, 0, 0, 1))
                    return None
                else: pass

                data = data[1:len(data)-1]  # cut these useless '()' out

                left = find_all_str('(', data)
                right = find_all_str(')', data)
                if len(left) != len(right):  # unmatched parethesis error
                    self._ConsoleOutput(
                        'SyntaxError: unmatched parenthesis found in expression', (1, 0, 0, 1))
                    return None
                # we need to split the list according to the parenthesis structure

                nl = len(left)
                for i in range(nl):
                    temp = data[left[i]:right[i]+1].replace(',', '|')
                    # the spaces compensate the index gap
                    temp = ' '+temp[1:len(temp)-1]+' '
                    data = data[:left[i]] + temp + data[right[i]+1:]

                Buffer += data.split(',')  # identify arguments
                for i in range(len(Buffer)):
                    Buffer[i] = Buffer[i].strip()
                    if '|' in Buffer[i]:
                        Buffer[i] = Buffer[i].split('|')  # internal tuples
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
                            # a recursive algorithm might have been a better option
                            for t in range(len(Buffer[j])):
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
                # several arguments have been provided
                if len(Buffer)-1 and Buffer[1] != '':
                    try:
                        ChosenCommand(*Buffer[1:])
                        return None
                    except TypeError:
                        self._ConsoleOutput(
                            "Wrong arguments provided", (1, 0, 0, 1))
                        return None
                else:
                    try:
                        ChosenCommand()
                        return None
                    except TypeError:
                        self._ConsoleOutput(
                            'This command requires (at least) one argument', (1, 0, 0, 1))
                        return None
            except:
                self._CommandError(Buffer[0])

        def cmd_process():
            nonlocal data, self
            command = Command(data.strip())
            try:
                output = command.run(timeout=1)
                self._ConsoleOutput(output[0])
                self._CMDError(output[1])
            except:
                self._CMDError(traceback.format_exc())

        if self._indicator['text'] == 'pyt> ':
            pyt_process()
        elif self._indicator['text'] == 'csl> ':
            csl_process()
        elif self._indicator['text'] == 'cmd> ':
            cmd_process()
        return None

    def _CMDError(self, report):
        if report == None: return
        elif type(report) is not str: report = str(report)
        else:
            sys.__stderr__.write(report)
            self._ConsoleOutput(report, (1, 0, 0, 1))
        return

    def _CommandError(self, report):
        self._ConsoleOutput("Pconsole (most recent call last):", (1, 0, 0, 1))
        self._ConsoleOutput("CommandError: command '" +
                            str(report)+"' is not defined", (1, 0, 0, 1))

    def _ConsoleOutput(self, output, color: Vec4 = Vec4(1, 1, 1, 1), mode: str = 'add', CMD_type=False, encoding='utf-8'):
        redistribute(self._SavedLines, self._maxsize,
                     self._maxlines, self._LinesOnDisplay)

        keyword = "\n"
        if output == None: return
        elif type(output) is bytes: output = convert(output, self.win_symbols)
        if CMD_type: sys.__stdout__.write(output)

        text = output.split(keyword)

        text = [[x[i:i+self._maxsize]
            for i in range(0, len(x), self._maxsize)] for x in text]
        if mode == 'add':
            for discretized in text:
                self._SavedLines.append((''.join(discretized), color))
                for i in range(len(discretized)):  # for each line
                    for x in range(self._maxlines-1, 0, -1):
                        self._LinesOnDisplay[x].textnode.text = self._LinesOnDisplay[x-1].textnode.text
                        self._LinesOnDisplay[x].textnode.fg = self._LinesOnDisplay[x-1].textnode.fg
                        self._LinesOnDisplay[x].lineIndex = self._LinesOnDisplay[x-1].lineIndex
                        self._LinesOnDisplay[x].charInterval = self._LinesOnDisplay[x-1].charInterval
                    self._LinesOnDisplay[0].textnode.text = discretized[i]
                    self._LinesOnDisplay[0].textnode.fg = color
                    self._LinesOnDisplay[0].lineIndex = len(
                        self._SavedLines)-1  # save the line number
                    previous = ''
                    # sum up all the previous chars
                    for t in range(i): previous += discretized[t]
                    self._LinesOnDisplay[0].charInterval = [
                        len(previous), len(previous)+len(discretized[i])-1]
        elif mode == 'edit':
            # save the line, might not work properly
            self._SavedLines[-1] = (output, color)
            for discretized in text:
                n = len(discretized)
                for i in range(n):
                    self._LinesOnDisplay[i].textnode.text = discretized[n - i - 1]
                    self._LinesOnDisplay[i].textnode.fg = color
                    self._LinesOnDisplay[i].lineIndex = len(
                        self._SavedLines)-1  # charinterval not handled
        return None

    def _scroll(self, direction: bool):
        sign = (-1)**int(direction+1)  # -1 or 1 depending on the boolean
        self._scrollingIndex = displace(
            self._SavedLines, self._maxsize, self._maxlines, self._LinesOnDisplay, self._scrollingIndex, sign)

    def _switch_adr(self):
        current = self._indicator['text']
        n = list(self.consoles.keys()).index(current)
        if n == len(self.consoles.keys())-1:
            n = 0
        else:
            n += 1
        self._indicator['text'] = list(self.consoles.keys())[n]
        self._info.text = "targeting: " + \
            self.consoles[self._indicator['text']]

    def _update_res(self):
        self.res = (base.win.getXSize(), base.win.getYSize(),
                    base.getAspectRatio())  # update res
        # update frame stuff
        # if self._maxsize < 10: return # we want the indicator to always stay inside the background frame
        self._Resframesize = [self._framesize[0]
            * self.res[2], self._framesize[1]]
        self._recomputeFrame()
        self._background.setScale(
            self._Resframesize[0]/self._framesize[0], 1, self._Resframesize[1]/self._framesize[1])
        # update text disposition
        redistribute(self._SavedLines, self._maxsize,
                     self._maxlines, self._LinesOnDisplay)
        self._scrollingIndex = 0  # reset scrolling
        self.entry['width'] = self._maxsize
        # debug
        if self._verbose: print('updated res to %s - x,y,ratio' % str(
            (base.win.getXSize(), base.win.getYSize(), base.getAspectRatio())))

    def _callBack(self, key: bool):
        invertedInput = self._InputLines[::-1]
        if key:  # up key pressed
            try:  # avoid out of range errors
                if self._callBackIndex < len(invertedInput):
                    self._callBackIndex += 1
                    self.entry.enterText(invertedInput[self._callBackIndex])
            except: pass
        else:
            try:
                if self._callBackIndex >= 0:
                    self._callBackIndex -= 1
                    self.entry.enterText(
                        ([''] + invertedInput)[self._callBackIndex])
            except: pass

    def _textToLine(self, text):
        try:
            text = text.replace("\n", "")
        except:
            pass
        return text

    def _recomputeFrame(self):
        def getfontbounds():
            nonlocal self
            temp = OnscreenText(text='1234567890', scale=self._textscale)
            bounds = temp.getTightBounds()
            temp.destroy()
            return bounds
        bounds = getfontbounds()
        width = (bounds[1][0] - bounds[0][0])/10
        self._maxsize = int(self._Resframesize[0]/width)
        self._maxlines = int((self._Resframesize[1]-0.12)/self._textscale) + 1

    def _versioncheck(self):
        # version_check
        if not self._check_version: return
        self._ConsoleOutput(" \nChecking for updates...", Vec4(0.8, 0.7, 0, 1))
        try:
            # load project json
            r = requests.get("https://pypi.org/pypi/pconsole/json")
            # load last version available (str format)
            latest = list(r.json()['releases'].keys())[-1]
        except:
            self._ConsoleOutput("failed to connect to the Pypi database via json protocol\n ", Vec4(0.8,0.7,0,1))
            return

        if latest != version and int(''.join(version.split('.'))) < int(''.join(latest.split('.'))):
            self._ConsoleOutput("This version of pconsole ({}) is outdated.\nPlease consider updating it using the command 'pip install pconsole'\n ".format(
                version), Vec4(0.8, 0.7, 0, 1))
        elif int(''.join(version.split('.'))) > int(''.join(latest.split('.'))):
            self._ConsoleOutput("This version of pconsole ({}) hasn't been released yet.\nIt may therefore contain some bugs.\nPlease consider installing a stable build using \n'pip install pconsole'\n ".format(version), Vec4(0.8,0.7,0,1))
        else:
            self._ConsoleOutput("This version of pconsole is currently up-to-date", Vec4(0.8,0.7,0,1))
        
        
    def usage(self,index):
        '''
        Provides help concerning a given command
        '''
        try:
            i = self.CommandDictionary[index]
            self._ConsoleOutput("Help concerning command '%s':" % str(index), color = (0.243,0.941,1,1))
            self._ConsoleOutput("- associated function name is '%s'" % str(i.__name__))
            self._ConsoleOutput("- Documentation provided: ")
            doc = self._textToLine(str(i.__doc__))
            if not doc == str(None):
                self._ConsoleOutput(doc.strip())
            else:
                self._ConsoleOutput("No docstring found")
            self._ConsoleOutput("- Known arguments: ")
            
            arg = list(i.__code__.co_varnames)
            # del arg[0] # remove the self argument
            arg = str(arg)
            if len(arg)-2:
                self._ConsoleOutput(str(arg)[1:len(str(arg))-1]) # remove brackets
            else:
                self._ConsoleOutput("No arguments required")
        except KeyError: # not in the dictionary
            self._ConsoleOutput("Unknown command '%s'" % str(index), (1,0,0,1))
        return None
    
    def help(self):
        '''
        Shows a list of available commands
        '''
        self._ConsoleOutput("List of available commands: ", color = (0.243,0.941,1,1))
        for i in self.CommandDictionary:
            self._ConsoleOutput("- "+str(i))
        self._ConsoleOutput(" ")
        self._ConsoleOutput("Use usage(command) for more details on a specific command")
        return None

    def credits(self):
        self._ConsoleOutput("Thanks to rdb, darthrigg, and the panda3d community for supporting this project.")
        self._ConsoleOutput("This program was created by l3alr0g. See https://github.com/l3alr0g/pconsole for more information.")
        self._ConsoleOutput("Download the panda3d engine at panda3d.org")

    def showLicense(self):
        with open(os.path.join(PYMAINDIR,'license.txt')) as l:
            license = l.read()
        self._ConsoleOutput(license, color = (1, 0.9, 0.7, 1))

def find_all_str(sample, string):
    n = len(sample)
    poslist = []
    for i in range(len(string)-n+1):
        if string[i:i+n] == sample:
            poslist.append(i)
        else:pass
    return poslist
