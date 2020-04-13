# panda3d console
 a tiny and easy-to-use runtime console for panda3d-powered apps

### Installation

```bash
pip install pconsole
```

or, alternatively

```bash
cd pckg dir
pip install -e .
```

### Initialize console

```python
import pconsole
commandDic = {"f1_string":f1,
              "f2_string":f2
}
myConsole = pconsole.Console()
myConsole.create(commandDic)
# command line is now up and running
```

### default commands

- help: lists all available commands
- usage: specific help
