from pconsole.console import Console
from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenImage import OnscreenImage
from threading import Thread
import os,sys

MAINDIR = Filename.from_os_specific(os.path.abspath(sys.path[0])).getFullpath()

class testApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.disable_mouse()
        self.mire = OnscreenImage(image = MAINDIR+ '/test.jpeg')
        self.mire.setScale(1.6, 1, 1)
        commandDic = {
            "test":testfunc
        }
        self.commandline = Console()
        self.commandline.create(commandDic, app = self)
        self.task_mgr.add(self.update, "updatingTask")
    
    def update(self, task):
        return task.cont

def testfunc():
    pass

App = testApp()
App.run()