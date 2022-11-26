import argparse
from typing import List, Callable, Optional, Union

from argParseFromDoc import get_parser_from_function


class AutoArgumentParser(argparse.ArgumentParser):
    def parse_args_groups(self, args=None, namespace=None):
        args = super().parse_args(args=args, namespace=namespace)
        arg_groups = {}
        for group in self._action_groups:
            group_dict = {a.dest: getattr(args, a.dest, None) for a in group._group_actions}
            arg_groups[group.title] = argparse.Namespace(**group_dict)
        return arg_groups

    def add_args_from_function(self, callable: Callable, new_group_name:Optional[str]=None,
                               args_to_ignore: List[str] = None,
                               args_to_include: List[str] = None,
                               args_optional: List[str] = None) -> Union["AutoArgumentParser", argparse._ArgumentGroup]:
        """

        :param callable: the documented function to extract information from
        :param new_group_name: A string if the function arguments should be added to a parser group or None otherwise
        :param args_to_ignore: Arguments in the function callable that won't be translated to argparse arguments
        :param args_to_include: Only this names of arguments in the function callable will be translated to argparse arguments
        :param args_optional: Arguments in the function callable that are optional.
        :return: the parser or the new group
        """
        if new_group_name is not None:
            group = self.add_argument_group(title=new_group_name)
        else:
            group = self
        get_parser_from_function(callable, args_to_ignore=args_to_ignore,
                                 args_to_include = args_to_include, args_optional=args_optional, parser=group)

        return group

    @staticmethod
    def parse_function_and_call(callable: Callable, args_to_ignore: List[str] = None,
                               args_to_include: List[str] = None, args_optional: List[str] = None):
        parse_function_and_call(callable, args_to_ignore, args_to_include, args_optional)


def parse_function_and_call(callable: Callable, args_to_ignore: List[str] = None,
                            args_to_include: List[str] = None, args_optional: List[str] = None):
    parser = AutoArgumentParser(callable.__name__)
    parser.add_args_from_function(callable, args_to_ignore=args_to_ignore,
                                  args_to_include=args_to_include, args_optional=args_optional)

    args = parser.parse_args()
    return callable(**vars(args))
