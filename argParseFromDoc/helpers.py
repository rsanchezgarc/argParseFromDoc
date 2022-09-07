import argparse
import inspect
import typing
from collections import OrderedDict
from typing import Callable, List, Optional, _GenericAlias


def _get_type_nargs_default_required_dict(callable: Callable, args_to_ignore: List[str], args_to_include: Optional[List[str]] = None):
    """
    Inspect the signature of a function to get the types of the arguments and the default value
    :param callable: The function to analyse
    :param args_to_ignore: Argument that should not be considered
    :param args_to_include: If provided, only the arguments in this list will be considered
    :return:
    """
    signature = inspect.signature(callable)
    name_to_type_nargs_default_required = OrderedDict()
    n_args = len(signature.parameters.items())
    items = signature.parameters.items()

    for i, (argname, v) in enumerate(items):

        if i == 0 and str(v) == "self":
            continue
        elif i == n_args-2 and str(v).replace(" ", "") == "*args":
            continue
        elif i == n_args-1 and str(v).replace(" ", "") == "**kwargs":
            continue

        if argname in args_to_ignore or (args_to_include is not None and argname not in args_to_include):
            name_to_type_nargs_default_required[argname] = None
            continue

        default = None if v.default is inspect.Parameter.empty else v.default
        _type, narg, required = fromTypeToTypeFun(v)
        assert argname not in name_to_type_nargs_default_required, "argParseFromDoc: Error, duplicated argument %s" % argname
        # if isinstance(_type, tuple): assert default is not None , "Error, Literal type hints cannot have None default"
        name_to_type_nargs_default_required[argname] = (_type, narg, default, required)

    return name_to_type_nargs_default_required


def fromTypeToTypeFun(typeHint):

    hintType = typeHint.annotation
    required = True
    nargs = None
    #Check optional or union
    if isinstance(hintType, _GenericAlias):
        complex_type = hintType._name
        if complex_type == "Optional" or complex_type is None: #Union type, or Literal type, depending on the version
            if hintType.__origin__ == typing.Union:
                # check if we are in Union[XXX,NoneType]
                inner_args = hintType.__args__
                assert len(inner_args) == 2, "Error, only Optional or Union[XXX,None] are valid options"
                valid=False
                for arg in inner_args:
                    if getattr(arg, "__name__", "") == 'NoneType':
                        valid = True
                    else:
                        hintType = arg
                assert valid, "Error, Union[XXX,None] is a valid option, but None was not present"
                required = False

    if isinstance(hintType, _GenericAlias):
        complex_type = hintType._name
        if complex_type == "Literal" or complex_type is None: #Union type, or Literal type, depending on the version
            if hintType.__origin__ == getattr(typing, "Literal", "Literal"):
                _type = tuple(hintType.__args__)
                return _type, nargs, required
            raise ValueError("Error, only Optional, Union and Literal type hints supported")


    if isinstance(hintType, _GenericAlias):
        complex_type = hintType._name
        assert complex_type in ["Tuple",
                                "List"], "argParseFromDoc: Error, only Tuple or List are supported, you used %s" % complex_type
        nargs = "+"
        inner_args = hintType.__args__
        assert len(inner_args) == 1, "argParseFromDoc: Error, only simple aggregated types supported"
        hintType = inner_args[0]

    assert not isinstance(hintType, _GenericAlias), "argParseFromDoc: Error, nested types are not supported"

    strType = hintType.__name__
    _type = _get_type_from_str(strType)
    if _type is None:
        raise ValueError("argParseFromDoc: Not supported type: %s (%s)" % (str(strType), typeHint))
    return _type, nargs, required


def _get_type_from_str(strType):
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
    elif isinstance(strType, str) and strType.startswith("list of"):
        _type = List[_get_type_from_str(strType.replace("list of", "").strip())]
    return _type
