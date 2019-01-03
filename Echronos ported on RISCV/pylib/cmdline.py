#
# eChronos Real-Time Operating System
# Copyright (c) 2017, Commonwealth Scientific and Industrial Research
# Organisation (CSIRO) ABN 41 687 119 230.
#
# All rights reserved. CSIRO is willing to grant you a licence to the eChronos
# real-time operating system under the terms of the CSIRO_BSD_MIT license. See
# the file "LICENSE_CSIRO_BSD_MIT.txt" for details.
#
# @TAG(CSIRO_BSD_MIT)
#

"""Tools for managing command line commands of x.py.

x.py's command line is structured by high-level commands, such as *test*, each of which have multiple sub-commands,
such as *systems*.
Each sub-command can have one or more arguments/options.
With the tools in this module, a function that implements a sub-command can be annotated with attributes that describe
its command-line command, sub-command, help string, and arguments:

    @subcmd(name='systems', cmd='test', help='Run system tests',
            args=(Arg('--verbose', action='store_true', default=False),))
    def system_tests():
        pass

"""

from types import ModuleType, FunctionType
from functools import wraps


class Arg:
    """Wrap arbitrary function arguments.

    With this class, one can store a collection of arbitrary unnamed and named function arguments with a minimum
    amount of code.
    The arguments can then, e.g., be passed on to another function call.

    In the case of command line parsing, Arg objects collect the arguments that go into the add_argument() method of
    command line parsers.

    """
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class cmd:  # pylint: disable=invalid-name
    """The @cmd() function decorator marks a function as the implementation of a command-line command of an
    executable."""
    def __init__(self, name=None, help=None, args=()):  # pylint: disable=redefined-builtin
        """Create a function decorator and wrapper for a function implementing a command-line command.

        For example, the command-line executable 'foo' may wish to implement a command-line command 'bar' with the
        option '--baz' invoked at the command line as 'foo bar --baz'.
        The arguments of this constructor allow to describe the command-line properties of the command in more
        detail.

        `name`: name of the command, e.g., 'bar'.
        It defaults to the name of the wrapped function.
        For example, when adding the @cmd decorator to the function `def bar()`, the default for the command's
        name is 'bar'.

        `help`: the help string for the command as it appears in the command-line help of the executable.

        `args`: a list or tuple of the arguments or options for the command.
        For example, to add the argument '--baz' to the command 'foo bar', `args` would have to have the list value
        [Arg('--baz')].
        For each Arg object, its contents are passed to the add_argument() function of the parser object for the
        sub-command.

        """
        self.name = name
        self.help = help
        self.args = args
        self.execute = None

    def __call__(self, wrapped_function):
        """Implementation of Python magic for wrapping functions."""
        # See functools.wraps() documentation
        @wraps(wrapped_function)
        def wrapper(*args, **kwds):
            return wrapped_function(*args, **kwds)
        # Let command name default to name of wrapped function
        if self.name is None:
            self.name = wrapped_function.__name__
        # Set function wrapper as handler for command
        self.execute = wrapped_function
        # Make decorator object and its properties accessible as an attribute of the function wrapper
        wrapper.decorator = self
        return wrapper


def add_commands_to_parser(global_attributes, parser):
    """Configure an argparse.ArgumentParser with commands and options based on the @cmd decorators found in the global
    attributes."""
    cmds = _get_cmds(global_attributes)
    _add_cmds_to_parser(cmds, parser)


def _get_cmds(global_attributes):
    yield from _get_decorators(global_attributes, cmd)


def _get_decorators(global_attributes, decorator_type):
    """From a globals() dictionary, find all functions with a decorator of a given type and retrieve its decorator
    objects."""
    # deliberately use type() to compare against decorator_type to avoid subcmd objects being returned when cmd
    # objects are requested
    for attribute in global_attributes.values():
        if isinstance(attribute, ModuleType):
            yield from [func.decorator for func in vars(attribute).values()
                        if isinstance(func, FunctionType) and hasattr(func, 'decorator') and
                        isinstance(func.decorator, decorator_type)]
        elif isinstance(attribute, FunctionType) and hasattr(attribute, 'decorator') \
                and isinstance(attribute.decorator, decorator_type):
            yield attribute


def _add_cmds_to_parser(cmds, parser, dest='command', title='commands'):
    """Configure an argparse.ArgumentParser based on cmd objects."""
    cmds_parsers = parser.add_subparsers(title=title, dest=dest)
    for command in cmds:
        cmd_parser = cmds_parsers.add_parser(command.name, help=command.help)
        for arg in command.args:
            cmd_parser.add_argument(*arg.args, **arg.kwargs)
        cmd_parser.set_defaults(execute=command.execute)


class subcmd(cmd):  # pylint: disable=invalid-name
    """The @subcmd() function decorator marks a function as the implementation of an x.py command-line sub-command."""
    # pylint: disable=redefined-builtin,redefined-outer-name
    def __init__(self, name=None, cmd=None, help=None, args=()):
        self.cmd = cmd
        super(subcmd, self).__init__(name=name, help=help, args=args)

    def __call__(self, wrapped_function):
        if self.cmd is None:
            self.cmd = wrapped_function.__module__.split('.')[-1]
        return super(subcmd, self).__call__(wrapped_function)


def add_subcommands_to_parser(global_attributes, parser):
    """Search global attributes for functions marked with @subcmd decorators and construct command-line parser"""
    cmd_tree = _get_cmd_tree(_get_subcmds(global_attributes))
    _add_cmd_tree_to_parser(cmd_tree, parser)


def _get_subcmds(global_attributes):
    """From x.py's globals() dictionary, retrieve the subcmd objects of all functions with the @subcmd decorator"""
    yield from _get_decorators(global_attributes, subcmd)


def _get_cmd_tree(subcmds):
    """Convert flat list of subcmd objects into hierarchical dictionary
    {'command name': {'subcommand name 1': subcmd1, 'subcommand name 2': subcmd2}}"""
    cmds = {}
    for sub_cmd in subcmds:
        cmd_dict = cmds.setdefault(sub_cmd.cmd, {})
        cmd_dict[sub_cmd.name] = sub_cmd
    return cmds


def _add_cmd_tree_to_parser(cmd_tree, parser):
    """Create command-line parser from hierarchical subcmd objects."""
    cmds_parsers = parser.add_subparsers(title='commands', dest='command')
    for command in sorted(cmd_tree.keys()):
        cmd_parser = cmds_parsers.add_parser(command)
        subcmds = sorted(cmd_tree[command].values(), key=lambda tmp: tmp.name)
        _add_cmds_to_parser(subcmds, cmd_parser, dest="subcommand", title=None)
