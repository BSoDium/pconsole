from .defaults import __blacklist__
import traceback
from .cmd_command import Command

def py_process(data, app, _os_error):
    _main = app  # defined so the user can access it from the commandline
    data = data.strip()
    forb = list(__blacklist__.keys())
    for a in forb:
        k = len(a)
        if data[:k] == a:
            _os_error(
                'Sorry, this command has been disabled internally\nReason:')
            _os_error(__blacklist__[a])
            return None
    try:
        exec(data.strip())
    except Exception:
        _os_error(traceback.format_exc())
    except SystemExit:
        pass
    return None

def csl_process(data, _output, _command_dictionary, _command_error):
    ind = data.find('(')
    Buffer = []
    if ind <= 0:  # no occurence
        Buffer.append(data)
    else:
        Buffer.append(data[0:ind])  # indentify keyword
        data = data[ind:len(data)]  # strip the string as we move along
        # closing parenthesis syntax stuff
        if not(data[0] == '(' and data[len(data)-1] == ')'):
            _output(
                'Missing parenthesis ")" in "' + Buffer[0] + data + '"', (1, 0, 0, 1))
            return None
        else: pass

        data = data[1:len(data)-1]  # cut these useless '()' out

        left = find_all_str('(', data)
        right = find_all_str(')', data)
        if len(left) != len(right):  # unmatched parethesis error
            _output(
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
        _chosencommand = _command_dictionary[Buffer[0]]
        # several arguments have been provided
        if len(Buffer)-1 and Buffer[1] != '':
            try:
                _chosencommand(*Buffer[1:])
                return None
            except TypeError:
                _output(
                    "Wrong arguments provided", (1, 0, 0, 1))
                return None
        else:
            try:
                _chosencommand()
                return None
            except TypeError:
                _output(
                    'This command requires (at least) one argument', (1, 0, 0, 1))
                return None
    except:
        _command_error(Buffer[0])


def cmd_process(data, _output, _os_error):
    
    command = Command(data.strip())
    try:
        output = command.run(timeout=1)
        _output(output[0])
        _os_error(output[1])
    except:
        _os_error(traceback.format_exc())