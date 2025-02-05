from typing import Any, Dict, List, Union, get_type_hints, TextIO, BinaryIO, Optional
import inspect
from pathlib import Path


def _get_inner_type(type_hint):
    """Helper to get the inner type from Optional types"""
    if str(type_hint).startswith('typing.Optional['):
        # Extract inner type from Optional[X]
        inner = str(type_hint)[16:-1]  # Remove 'typing.Optional[' and ']'
        if inner.startswith('typing.List['):
            return 'typing.List[' + inner[12:]  # Keep the List[] wrapper
        return inner
    return str(type_hint)


def generate_args_for_argparseFromDoc(fun, **kwargs) -> List[str]:
    type_hints = get_type_hints(fun)
    sig = inspect.signature(fun)
    cmd_args = []

    args_optional = kwargs.pop('args_optional', [])
    args_to_ignore = kwargs.pop('args_to_ignore', [])
    args_to_include = kwargs.pop('args_to_include', None)

    parameters = sig.parameters
    if args_to_include:
        parameters = {k: v for k, v in parameters.items() if k in args_to_include}
    parameters = {k: v for k, v in parameters.items() if k not in args_to_ignore}

    for name, param in parameters.items():
        if name == 'self':
            continue

        is_optional = (
            param.default != inspect.Parameter.empty or
            name in args_optional or
            str(type_hints[name]).startswith('typing.Optional')
        )

        if name not in kwargs:
            if not is_optional:
                raise ValueError(f"Required argument '{name}' not provided")
            continue

        value = kwargs[name]
        if is_optional and value is None:
            continue

        param_type = type_hints.get(name)
        inner_type = _get_inner_type(param_type)

        if inner_type == 'bool' or inner_type == "<class 'bool'>":
            default_value = param.default if param.default != inspect.Parameter.empty else False
            if value != default_value:  # Only add flag if it differs from default
                if default_value:
                    cmd_args.append(f'--NOT_{name}')
                else:
                    cmd_args.append(f'--{name}')
            continue

        cmd_args.append(f'--{name}')

        if inner_type.startswith('typing.List'):
            if not isinstance(value, (list, tuple)):
                raise ValueError(f"Argument '{name}' should be a list")
            cmd_args.extend(str(item) for item in value)
        elif param_type in (TextIO, BinaryIO):
            if hasattr(value, 'name'):
                cmd_args.append(value.name)
            else:
                cmd_args.append(str(value))
        else:
            cmd_args.append(str(value))

    return cmd_args


def generate_command_for_argparseFromDoc(
        path: Union[str, Path],
        fun,
        use_module: bool = False,
        python_executable: str = "python",
        **kwargs
) -> str:
    """
    Generate a complete command string for running a script/module with argParseFromDoc arguments.

    Args:
        path: Path to the Python script or module name
        fun: The function to generate arguments for
        use_module: If True, use -m to run as module instead of as script
        python_executable: Python executable to use (default: "python")
        **kwargs: The arguments to pass to the function

    Returns:
        str: The complete command string that can be used with subprocess

    Examples:
        # Run as script
        cmd = generate_command_for_argparseFromDoc('script.py', add, a=5, b=["hello", "world"])
        # Returns: 'python script.py --a 5 --b hello world'

        # Run as module
        cmd = generate_command_for_argparseFromDoc('my_package.script', add, use_module=True, a=5, b=["hello"])
        # Returns: 'python -m my_package.script --a 5 --b hello'
    """
    args = generate_args_for_argparseFromDoc(fun, **kwargs)

    if use_module:
        return f"{python_executable} -m {path} {' '.join(args)}"
    else:
        return f"{python_executable} {path} {' '.join(args)}"