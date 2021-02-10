import sys

class ParenthesisError(Exception):
    pass

def os_error(report, _output):
    """
    Display os terminal report 
    """
    if report == None: return
    elif type(report) is not str: report = str(report)
    else:
        sys.__stderr__.write(report)
        _output(report, (1, 0, 0, 1))

def command_error(report, _output):
    _output("Pconsole (most recent call last):", (1, 0, 0, 1))
    _output("CommandError: command '%s' is not defined" % str(report), (1, 0, 0, 1))

def parenthesis_error(_output):
    _output('SyntaxError: unmatched group separator found in expression', (1, 0, 0, 1))

def syntax_error(report, _output):
    _output('SyntaxError: incoherent use of command %s' % str(report), (1, 0, 0, 1))

def args_error(_output):
    _output('ArgumentError: invalid arguments ', (1, 0, 0, 1))