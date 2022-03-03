import argparse
from typing import List, Callable

from argParseFromDoc import get_parser_from_function


class AutoArgumentParser(argparse.ArgumentParser):
    def parse_args_groups(self, args=None, namespace=None):
        args = super().parse_args(args=args, namespace=namespace)
        arg_groups = {}
        for group in self._action_groups:
            group_dict = {a.dest: getattr(args, a.dest, None) for a in group._group_actions}
            arg_groups[group.title] = argparse.Namespace(**group_dict)
        return arg_groups

    def add_args_from_function(self, callable: Callable, new_group_name=None, args_to_ignore: List[str] = None,
                               args_to_include: List[str] = None, args_optional: List[str] = None):
        if new_group_name is not None:
            group = self.add_argument_group(title=new_group_name)
        else:
            group = self
        get_parser_from_function(callable, args_to_ignore=args_to_ignore,
                                 args_to_include = args_to_include, args_optional=args_optional, parser=group)