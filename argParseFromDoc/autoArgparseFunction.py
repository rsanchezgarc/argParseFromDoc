from argparse import ArgumentParser, _ArgumentGroup
from typing import Callable, List, Union

from docstring_parser import parse


# TODO: document all functions
from argParseFromDoc.helpers import _get_type_nargs_default_required_dict, _get_type_from_str


def get_parser_from_function(callable: Callable, args_to_ignore: List[str] = None, args_to_include: List[str] = None,
                             args_optional: List[str] = None,
                             parser: Union[ArgumentParser, _ArgumentGroup] = None, *args, **kwargs):
    if parser is None:
        parser = ArgumentParser(*args, **kwargs)

    assert hasattr(callable, "__doc__"), "argParseFromDoc: Error, __doc__ missing in callable %s" % callable


    docstring = callable.__doc__
    docstring = parse(docstring)

    if args_to_ignore is None:
        args_to_ignore = set([])

    if args_to_include is None:
        args_to_include = set([(elem.arg_name) for elem in docstring.params])

    defaults_to_include_docstr = {elem.arg_name:elem.default for elem in docstring.params}
    typeNames_to_include_docstr = {elem.arg_name:elem.type_name for elem in docstring.params}

    name_to_type_nargs_default_dict = _get_type_nargs_default_required_dict(callable, args_to_ignore, args_to_include)


    if args_optional is None:
        args_optional = set([])

    params = []

    names_in_doc = [(elem.arg_name) for elem in docstring.params]
    keys_list = list(name_to_type_nargs_default_dict.keys())
    msg = ""
    for i in range(max(len(names_in_doc ), len(name_to_type_nargs_default_dict))):
        try:
            docname = names_in_doc[i]
        except IndexError:
            docname = "----"
        try:
            sig_name = keys_list[i]
            sig_values = name_to_type_nargs_default_dict.get(sig_name, "****")
        except IndexError:
            sig_name = "****"
            sig_values = None
        msg += "%20s\t%10s %20s\n"%(docname, sig_name, sig_values)
        if sig_values is None:
            continue
        type_, nargs, default, required = sig_values
        try:
            docstringType = _get_type_from_str(typeNames_to_include_docstr[sig_name] )
            if hasattr(docstringType, "_name") and docstringType._name == "List":
                docstringType = docstringType.__args__[0]
                assert nargs == "+"
                assert True, "Error, number of arguments mismatch between documentation (%s) and signature (%s) for %s" % (
                "+", nargs, sig_name)
            #TODO: what to do if docu says nothing about list of
            # else:
            #     assert nargs==1 or nargs is None, "Error, number of arguments mismatch between documentation (%s) and signature (%s) for %s" % (
            #     "None", nargs, sig_name)

            assert docstringType is None or docstringType == type_, "Error, type mismatch between documentation (%s) and signature (%s) for %s"%(docstringType , type_, sig_name)
        except KeyError:
            assert False, "Error, type mismatch between documentation (%s) and signature (%s) for %s" % (
            "None", type_, sig_name)

    error_msg_for_mismatch = "argParseFromDoc: Error, mismatch between type hints and" \
                             " documentation params.\ndocumentation\ttype_hints_name\ttype_hints_info:\n%s" % (msg)

    assert names_in_doc == list(name_to_type_nargs_default_dict.keys()), error_msg_for_mismatch

    seen_doc_params = set([])
    for elem in docstring.params:
        assert elem.arg_name not in seen_doc_params, "argParseFromDoc: Error, duplicated argument %s" % elem.arg_name
        seen_doc_params.add(elem.arg_name)
        if elem.arg_name not in args_to_ignore and elem.arg_name in args_to_include:
            info_from_signature = name_to_type_nargs_default_dict[elem.arg_name]
            if info_from_signature is None:
                continue
            typeFun, nargs, default, required = info_from_signature
            params.append((elem.arg_name, typeFun, nargs, default, elem.description, required))

    for paramTuple in params:
        name, typeFun, nargs, default, help, required = paramTuple

        required = (name not in args_optional and default is None) if required == True else False

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
        elif isinstance(typeFun, tuple):
            parser.add_argument("--" + name, choices=typeFun, help=help + " Default=%(default)s",
                                default=default,
                                required= required)
        else:
            parser.add_argument("--" + name, type=typeFun, nargs=nargs, help=help + " Default=%(default)s",
                                default=default,
                                required= required)

    return parser
