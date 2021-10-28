# argParseFromDoc

A simple python package for creating/updating [argparse](https://docs.python.org/3/library/argparse.html)
ArgumentParser(s) given a documented function.

## Content

- [Installation](#Installation)
- [Supported features](#Supported-features)
- [Assumptions](#Assumptions)
- [Usage](#Usage)

### Installation

- Option 1. Cloning this repository:
```
git clone https://github.com/rsanchezgarc/argParseFromDoc.git
cd argParseFromDoc
pip install .
```
- Option 2. Installing with pip
```
pip install git+https://github.com/rsanchezgarc/argParseFromDoc
```

### Supported features

- Argument types:
  - `int`, `str`, `float` and `bool`
  - (Homogeneous) Lists of any of the previous types (defined as`typing.List[primitive_type]`)
  - Files (defined as`typing.TextIO` and `typing.BinaryIO`)
- Ignoring/selecting a subset of the arguments of the function
- Creating a new parser or adding new arguments to it
- Several docsctring formats (see [docstring_parser](https://github.com/rr-/docstring_parser) )
- Support for methods assuming first argument in definition is `self`

### Assumptions
  - Positional arguments. Functions can have positional arguments, but the parser will treat them as 
    if they were keyword/optional (always `--argname VALUE`)
  - If no default value is provided for an argument in the typing hint, argument will be considered as
    required (`parser.add_argument(..., required=True)`). The same applies to `default=None` except if the
    name of the argument is included in `args_optional`. E.g `get_parser_from_function(..., args_optional=[name1, name2...])`  
  - Boolean arguments:
    - Boolean arguments must be provided with default value.
    - If a boolean argument defaults to False (`name:bool=False`), the parser sets
    the argument `name=True` if `--name` flag provided.
    - If a boolean argument defaults to True (`name:bool=True`), the parser sets
    the argument `name=False` if `--NOT_name` flag provided. Please notice that the name of
    the argument in the argument parser has been changed from `name` to `--NOT_name` to reflect that
    but the argument is stored using the original name, so
    no further changes are required
  - Multiple arguments can be provided if using `typing.List`. For example:
        `def fun(several_strings: List[str]):`
  - Setting deafult values for `typing.TextIO` and `typing.BinaryIO` is not advisable, as they should be opened files. 
    If you are only employing the function for the argument parser, you could default it to
    string values pointing files, but again, this is not encouraged. Instead, if you want to set a default filename,
    use type `str`. The main purpose of `typing.TextIO` and `typing.BinaryIO` in the parser is to allow pipes. For example:
    ```
    #These two commands are equivalent
    python count_lines --inputFile /etc/passwd 
    cat /etc/passwd | python count_lines --inputFile -
 
    ```
  - Methods, including `__init__`, are supported providing self is always using in as the first 
    argument in the definition
  - When defining functions, `*arg` and `**kwargs` are ignored for the parser. No other `*` or `**` argument
    is supported.

### Usage

You only need to document the type and possible default values for the arguments of your functions
with [typing](https://docs.python.org/3/library/typing.html) and the description of each within the docstring.
Examples of documented functions are:

```
def add(a: int, b: int):
    '''
    @param a: first number
    @param b: second number
    '''
    return a + b
    
def printYourAge(age: int, name: str = "Unknown"):
    '''
    @param age: your age
    @param name: your name
    '''
    return a + b
    
def addList(several_nums: List[int], b: int=1):
    '''
    @param several_nums: first number
    @param b: second number
    '''
    return [a + b for a in several_nums]

```

Then, obtaining an ArgumentParser for any of these functions (say `add`) is as easy as:

```
if __name__ == "__main__":
    from argParseFromDoc import get_parser_from_function
    parser = get_parser_from_function(add)
    args = parser.parse_args()
    print(add(**vars(args)))
```

If you want to add to a previously instantiated parser the arguements of the function,
you just need to provide the original parser (or group) to the `get_parser_from_function` function.

```
if __name__ == "__main__":
    from argParseFromDoc import get_parser_from_function
    #standard ArgumentParser
    from argparse import ArgumentParser
    parser = ArgumentParser(prog="Add_example")
    parser.add_argument("--other_type_of_argument", type=str, default="Not provided")
    #####################################################
    # ### If you prefer a group instead of a whole parser
    # group = parser.add_argument_group()
    # get_parser_from_function(add, parser=group)
    #####################################################
    #provide the original parser to get_parser_from_function that will add the new options to the parser
    get_parser_from_function(add, parser=parser)
    args = parser.parse_args()
    print(add(**vars(args)))
```
Finally, if your function has some arguments that you do not want to include
to the parser, you can use the `args_to_ignore` or `args_to_include options`. 

```
def manyArgsFun(a: int, b: int, c: int = 1, d: int = 2, e: str = "oneStr"):
    '''

    :param a: a
    :param b: b
    :param c: c
    :param d: d
    :param e: e
    :return:
    '''
    print(e)
    return sum([a, b, c, d])


if __name__ == "__main__":
    from argParseFromDoc import get_parser_from_function
    # parser = get_parser_from_function(manyArgsFun, args_to_ignore=["c", "d", "e"])
    parser = get_parser_from_function(manyArgsFun, args_to_include=["a", "b"])
    args = parser.parse_args()
    print(manyArgsFun(**vars(args)))

```


Some additional examples can be found in [examples folder](examples)