import requests
import inspect
import pathlib
import os
from panda3d.core import Vec4
from .version import __version__ as version

temp = os.path.dirname(__file__)
PYMAINDIR = str(pathlib.Path(temp).resolve())

class Utils:
    """
    Delocalized functions, used during console boot-up and at 
    runtime, such as help, usage, etc...
    """
    def __init__(self, output : callable) -> None:
        """
        Constructs and returns a new :class:`Utils`.
        """
        self._ConsoleOutput : callable = output
        self._check_version : bool = False
        self._command_dictionary : dict = {}
    
    @property
    def check_version(self) -> bool:
        """
        `Utils._check_version` getter
        """
        return self._check_version
    
    @property
    def command_dictionary(self) -> dict:
        """
        `Utils._command_dictionary` getter
        """
        return self.command_dictionary
    
    @check_version.setter
    def check_version(self, state : bool) -> None:
        """
        `Utils._check_version` setter
        """
        self._check_version = state
    
    @command_dictionary.setter
    def command_dictionary(self, command_dict : dict) -> None:
        """
        `Utils._command_dictionary` setter
        """
        self._command_dictionary = command_dict

    def _versioncheck(self):
        # version_check
        if not self._check_version: return
        self._ConsoleOutput(" \nChecking for updates...", Vec4(0.8, 0.7, 0, 1))
        try:
            # load project json
            r = requests.get("https://pypi.org/pypi/pconsole/json")
            # load last version available (str format)
            latest = list(r.json()['releases'].keys())[-1]
        except Exception:
            self._ConsoleOutput("failed to connect to the Pypi database via json protocol\n ", Vec4(0.8,0.7,0,1))
            return

        if latest != version and int(''.join(version.split('.'))) < int(''.join(latest.split('.'))):
            self._ConsoleOutput("This version of pconsole ({}) is outdated.\nPlease consider updating it using the command 'pip install pconsole'\n ".format(
                version), Vec4(0.8, 0.7, 0, 1))
        elif int(''.join(version.split('.'))) > int(''.join(latest.split('.'))):
            self._ConsoleOutput("This version of pconsole ({}) hasn't been released yet.\nIt may therefore be unstable.\nUse it at you own risk.".format(version), Vec4(0.8,0.7,0,1))
        else:
            self._ConsoleOutput("This version of pconsole is currently up-to-date", Vec4(0.8,0.7,0,1))
        
        
    def usage(self, command_name):
        '''
        Provides help concerning a given command
        '''
        try:
            i = self._command_dictionary[command_name]
            self._ConsoleOutput("Help concerning command '%s':" % str(command_name), color = (0.243,0.941,1,1))
            self._ConsoleOutput("- associated function name is '%s'" % str(i.__name__))
            self._ConsoleOutput("- Documentation provided: ")
            doc = self._text_to_line(str(i.__doc__))
            if not doc == str(None):
                self._ConsoleOutput(doc.strip(), (0.7, 0.9, 0.9, 1))
            else:
                self._ConsoleOutput("No docstring found", (1, 0, 0, 1))
            self._ConsoleOutput("- Known arguments: ")
            
            arg = list(str(inspect.signature(i))[1:-1].split(",")) 
            arg = ', '.join(arg)
            if len(arg) != 0:
                self._ConsoleOutput(str(arg)[1:len(str(arg))-1]) # remove brackets
            else:
                self._ConsoleOutput("No arguments required", (0.1, 1, 0.1, 1))
        except KeyError: # not in the dictionary
            self._ConsoleOutput("Unknown command '%s'" % str(index), (1,0,0,1))
        return None
    
    def help(self):
        '''
        Shows a list of available commands
        '''
        self._ConsoleOutput("List of available commands: ", color = (0.243,0.941,1,1))
        for i in self._command_dictionary:
            self._ConsoleOutput("- "+str(i))
        self._ConsoleOutput(" ")
        self._ConsoleOutput("Use usage(command) for more details on a specific command")
        return None

    def credits(self):
        self._ConsoleOutput("Thanks to rdb, darthrigg, and the panda3d community for supporting this project.")
        self._ConsoleOutput("This program was created by l3alr0g. See https://github.com/l3alr0g/pconsole for more information.")
        self._ConsoleOutput("Download the panda3d engine at panda3d.org")

    def show_license(self):
        with open(os.path.join(PYMAINDIR,'license.txt')) as l:
            _license = l.read()
        self._ConsoleOutput(_license, color = (1, 0.9, 0.7, 1))

    def _text_to_line(self, text):
        try:
            text = text.replace("\n", "")
        except Exception:
            pass
        return text