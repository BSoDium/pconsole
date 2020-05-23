# panda3d console
 a tiny and easy-to-use runtime console for panda3d-powered apps

### Installation

```bash
pip install pconsole
```

### Initialize console

```python
import pconsole
commandDic = {"func1_string":func1, # "associated string" : function name
              "func2_string":func2
}
key = 't' # this key will toggle the console, by default, pconsole will use 'f1'
myConsole = pconsole.Console()
myConsole.create(commandDic, event = key)
# command line is now up and running
```

### default commands

- help: lists all available commands

- usage: specific help

### additional features

use the 'app' argument when creating the console in order to be able to access attributes and variables from your main class in the python interpreter:

```python
myConsole.create(commandDic, event = key, app = self) # the self keyword will be refered to as 'main' in the interpreter
```

