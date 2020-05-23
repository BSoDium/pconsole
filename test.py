from pconsole.console import Console
from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenImage import OnscreenImage
from threading import Thread
import os,sys
from pconsole.inputfield import InputField

MAINDIR = Filename.from_os_specific(os.path.abspath(sys.path[0])).getFullpath()

class testApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.disable_mouse()
        self.mire = OnscreenImage(image = MAINDIR+ '/test.jpeg')
        self.mire.setScale(1.6, 1, 1)
        self.mire.hide()
        self.is_shown = False
        
        commandDic = {
            "toggleImage":self.toggleImage
        }
        self.commandline = Console()
        self.commandline.create(commandDic, app = self, event = 'f1')
        self.task_mgr.add(self.update, "updatingTask")

        '''
        # inputfield stuff
        props_mgr = TextPropertiesManager.get_global_ptr()
        col_prop = TextProperties()
        col_prop.set_text_color((1., 1., 1., 1.))
        props_mgr.set_properties("white", col_prop)

        pos = Vec3(-.5, 0., 0.)
        scale = .3
        width = 4.

        geoms = NodePath("input_field_geoms")

        cm = CardMaker("inputfield_geom_normal")
        cm.set_frame(0., width, -.5, 1.)
        cm.set_color(.5, .5, .5, 1.)
        cm.set_has_uvs(False)
        cm.set_has_normals(False)
        geoms.attach_new_node(cm.generate())

        cm = CardMaker("inputfield_geom_hilited")
        cm.set_frame(0., width, -.5, 1.)
        cm.set_color(.8, .8, .8, 1.)
        cm.set_has_uvs(False)
        cm.set_has_normals(False)
        geoms.attach_new_node(cm.generate())

        # Define a function that will be called when committing the entry text

        def on_commit_func(text, field_name):

          print(f"The following has been entered into {field_name}:", text)

        def on_keystroke(text):

          print("The following has been typed:", text)

        # Create two input fields
        self.buttonThrowers[0].node().set_keystroke_event("keystroke_event")
        self.accept("keystroke_event", on_keystroke)

        on_commit = (on_commit_func, ["inputfield_1"])
        self.field1 = InputField(self, pos, scale, width, geoms, on_commit)

        pos = Vec3(-.5, 0., .5)
        on_commit = (on_commit_func, ["inputfield_2"])
        self.field2 = InputField(self, pos, scale, width, geoms, on_commit)
        '''
        
    def update(self, task):
        return task.cont
    
    def toggleImage(self):
        if self.is_shown:
            self.mire.hide()
        else:
            self.mire.show()
        self.is_shown = not self.is_shown

def testfunc():
    '''I like grapes'''
    pass

App = testApp()
try: App.run()
except SystemExit:
    pass

# bug report: quand une entité ligne ne peut rentrer dans l'ecran a 100%, le resizing crash, voir commande
# driverquery ou help dans le cmd