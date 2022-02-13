"""
## Panda3D console
A tiny and easy-to-use runtime console for panda3d-powered apps.
### Initialize console
>>> commandDic = {"func1_string":func1,
...               "func2_string":func2}
>>> key = "t" # by default, pconsole will use "f1"
>>> myConsole = pconsole.Console()
>>> myConsole.create(commandDic, event = key, app = myApp)

### Default commands
- `help` : list all available commands
- `usage` : help on a specific command (requires docstring)
- `credits` : show credits
- `license` : display license file 

### Runtime usage
Use "f1" to toggle the console display (or the key chosen when calling 
:function:`create`) and "f2" to change the input stream

### Issues and Feedback
Please visit https://github.com/l3alr0g/pconsole to report a bug / 
suggest a new feature. Keep in mind that this project is still under 
developement and might not always behave as expected
"""

from .console import Console
from .version import __version__ as v

__title__ = 'console'
__author__ = 'l3alr0g'
__license__ = 'MIT'
__version__ = v