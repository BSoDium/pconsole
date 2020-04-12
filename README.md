# panda3d console
 a tiny and easy to use runtime console for panda3d-powered apps

### Installation

```
cd pckg dir
pip install -e .
```

### Initialize console

```
import pconsole
commandDic = {"command_string":associatedfunction,
"another_one":associatedfunction
}
myConsole = pconsole.Console()
myConsole.create(commandDic)
# command line is now up and running
```

### default commands

- help: lists all available commands
- usage: specific help