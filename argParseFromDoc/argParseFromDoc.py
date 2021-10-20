import abc
import argparse
import inspect
from argparse import ArgumentParser, _ArgumentGroup
from collections import OrderedDict
from typing import Callable, List, _GenericAlias, Union

from docstring_parser import parse


# TODO: document all functions

def _get_type_nargs_default_dict(callable: Callable):
    signature = inspect.signature(callable)
    name_to_type_nargs_default = OrderedDict()
    for k, v in signature.parameters.items():
        default = None if v.default is inspect.Parameter.empty else v.default
        _type, narg = fromTypeToTypeFun(v.annotation)
        assert k not in name_to_type_nargs_default, "argParseFromDoc: Error, duplicated argument %s" % k
        name_to_type_nargs_default[k] = (_type, narg, default)

    return name_to_type_nargs_default


def fromTypeToTypeFun(docuType):

    if isinstance(docuType, _GenericAlias):
        # if i
        complex_type = docuType._name
        assert complex_type in ["Tuple",
                                "List"], "argParseFromDoc: Error, only Tuple or List are supported, you used %s" % complex_type
        nargs = "+"
        inner_args = docuType.__args__
        assert len(inner_args) == 1, "argParseFromDoc: Error, only simple aggregated types supported"
        docuType = inner_args[0]
        assert not isinstance(docuType, _GenericAlias), "argParseFromDoc: Error, nested types are not supported"
    else:
        nargs = None

    strType = docuType.__name__
    _type = None
    if strType == "str":
        _type = str
    elif strType == "float":
        _type = float
    elif strType == "int":
        _type = int
    elif strType == "bool":
        _type = bool
    elif strType == "TextIO":
        _type = argparse.FileType('r')
    elif strType == "BinaryIO":
        _type = argparse.FileType('rb')
    else:
        raise ValueError("argParseFromDoc: Not supported type: " + str(strType))
    return _type, nargs


def get_parser_from_function(callable: Callable, args_to_ignore: List[str] = None, args_to_include: List[str] = None,
                             parser: Union[ArgumentParser, _ArgumentGroup] = None, *args, **kwargs):
    if parser is None:
        parser = ArgumentParser(*args, **kwargs)

    assert hasattr(callable, "__doc__"), "argParseFromDoc: Error, __doc__ missing in callable %s" % callable

    name_to_type_nargs_default_dict = _get_type_nargs_default_dict(callable)

    docstring = callable.__doc__
    docstring = parse(docstring)

    if args_to_ignore is None:
        args_to_ignore = set([])

    if args_to_include is None:
        args_to_include = set([(elem.arg_name) for elem in docstring.params])

    params = []

    names_in_doc = [(elem.arg_name) for elem in docstring.params]

    error_msg_for_mismatch = "argParseFromDoc: Error, mismatch between type hints and" \
                             " documentation params.\ndocumentation: %s\ntype hits: %s" % (
                             str(names_in_doc), tuple(name_to_type_nargs_default_dict.items()))

    assert names_in_doc == list(name_to_type_nargs_default_dict.keys()), error_msg_for_mismatch

    seen_doc_params = set([])
    for elem in docstring.params:
        assert elem.arg_name not in seen_doc_params, "argParseFromDoc: Error, duplicated argument %s" % elem.arg_name
        seen_doc_params.add(elem.arg_name)
        if elem.arg_name not in args_to_ignore and elem.arg_name in args_to_include:
            typeFun, nargs, default = name_to_type_nargs_default_dict[elem.arg_name]
            params.append((elem.arg_name, typeFun, nargs, default, elem.description))

    for paramTuple in params:
        name, typeFun, nargs, default, help = paramTuple
        if typeFun == bool:
            assert default is not None, "Error, bool arguments need to have associated default value. %s does not" % name
            if default is True:
                action = "store_false"
                varname = "NOT_" + name
            else:
                action = "store_true"
                varname = name
            help += " Action: " + action + " for variable %s" % name
            parser.add_argument("--" + varname, help=help, action=action, dest= name)
        else:
            parser.add_argument("--" + name, type=typeFun, nargs=nargs, help=help + " Default=%(default)s",
                                default=default,
                                required=default is None)

    return parser
