from .defaults import __blacklist__
import traceback
from .cmd_command import Command
from .error import parenthesis_error, command_error, os_error, syntax_error, args_error, ParenthesisError

def py_process(data, app, _output):
    """
    Process the provided data and send it to the Python interpreter.
    """
    _main = app  # defined so the user can access it from the commandline
    data = data.strip()
    forb = list(__blacklist__.keys())
    for a in forb:
        k = len(a)
        if data[:k] == a:
            os_error('Sorry, this command has been disabled internally\nReason:', _output)
            os_error(__blacklist__[a], _output)
            return None
    try:
        exec(data.strip())
    except Exception:
        os_error(traceback.format_exc(), _output)
    except SystemExit:
        pass
    return None


def csl_process(data, _output, _command_dictionary):
    """
    Process the provided data and execute the associated pconsole command.
    """
    
    assert type(data) is str
    # remove unnecessary spaces
    data = data.strip()
    # check for unbalanced parenthesis
    _group_separators = [
        ['(', '{', '['],
        [')', '}', ']']
    ]
    _balance = []
    for _ in data:
        if _ in _group_separators[0]:
            _balance.append(_)
        elif _ in _group_separators[1]:
            if len(_balance) == 0 or _group_separators[0].index(_balance[-1]) != _group_separators[1].index(_):
                parenthesis_error(_output)
                return 1
            else:
                del(_balance[-1])
    if len(_balance) != 0:
        parenthesis_error(_output)

    # recover main command
    _command_end_index = data.find("(")
    if _command_end_index != -1:
        _command = data[:_command_end_index]
    else: 
        _command = data
        _command_end_index = len(data)
    _executable = _command_dictionary[_command]
    
    # identify arguments
    _args = data[_command_end_index:]

    # check if last char is a parenthesis
    if len(_args) and _args[-1] != ')':
        syntax_error(_command, _output)
    
    # process arguments
    _args = _args[1:-1] # remove external parenthesis
    _args = clever_split(_args)
    for i in range(len(_args)):
        _args[i] = _args[i].strip()
    _args = convert(_args)
    
    # execute command 
    if len(_args) != 0:
        try:
            _executable(*_args)
        except Exception:
            args_error( _output)
    else:
        try:
            _executable()
        except Exception:
            args_error(_output)
    return 0

def cmd_process(data, _output):
    """
    Process the provided data and execute the associated os terminal command.
    """
    command = Command(data.strip())
    try:
        output = command.run(timeout=1)
        _output(output[0])
        os_error(output[1], _output)
    except Exception:
        os_error(traceback.format_exc(), _output)

def convert(args_list):
    """
    Convert each element of a given list to the best fitting type (int, float, string...)
    Warning : this algorithm is recursive and is therefore the only source of infinite recursion in this package
    """
    
    for _ in range(len(args_list)):
        # check if the element is a branch or a leaf
        test = '(' in args_list[_] or '[' in args_list[_] or '{' in args_list[_]
        if test: # branch
            args_list[_] = clever_split(args_list[_][1:-1])
            for i in range(len(args_list[_])):
                args_list[_][i] = args_list[_][i].strip()
            args_list[_] = convert(args_list[_])
        else: # leaf
            try:
                args_list[_] = int(args_list[_])
            except ValueError:
                try:
                    args_list[_] = float(args_list[_])
                except ValueError:
                    pass # keep a string
    return args_list


def clever_split(string):
    """
    Split a string on ',' it contains, as long as it is out of a parenthesis block
    """
    _group_separators = [
        ['(', '{', '['],
        [')', '}', ']']
    ]
    index_list = []
    output_list = []
    i = 0
    while i < len(string):
        if string[i] == ',':
            if len(index_list): output_list.append(string[index_list[-1]+1:i])
            else: output_list.append(string[:i])
            index_list.append(i)
        elif string[i] in _group_separators[0]:
            _balance = [string[i]]
            # go to the corresponding closing parenthesis
            while len(_balance) > 0:
                i += 1
                if string[i] in _group_separators[0]:
                    _balance.append(string[i])
                elif string[i] in _group_separators[1]:
                    if _group_separators[0].index(_balance[-1]) == _group_separators[1].index(string[i]):
                        del(_balance[-1])
                    else:
                        raise ParenthesisError
        i += 1
    if len(index_list): output_list.append(string[index_list[-1]+1:]) # last element
    else: output_list.append(string)
    return output_list

