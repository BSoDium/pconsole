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
        self.mire = OnscreenImage(image = MAINDIR+ '/test.jpg')
        self.mire.setScale(1.3, 1, 1)
        commandDic = {
            "test":self.__init__
        }
        self.commandline = Console()
        self.commandline.create(commandDic)
        self.task_mgr.add(self.update, "updatingTask")
    
    def update(self, task):
        return task.cont
    
a = testApp()
a.run()