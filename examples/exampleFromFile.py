from typing import BinaryIO, TextIO


# TextIO/BinaryIO default shuldn't be a string if the function is going to be called within the program, but can be done
# for automatic parsing.
def count_nlines(a: TextIO, b: BinaryIO):
    '''
    @param a: text file
    @param b: binary file
    '''
    print(a.name, b.name)
    return len(a.readlines())


if __name__ == "__main__":
    from argParseFromDoc import parse_function_and_call
    out = parse_function_and_call(count_nlines)
    print(out)

    '''
python -m examples.exampleFromFile --a examples/exampleFromFile.py  --b examples/__pycache__/exampleFromFile.cpython-37.pyc
cat examples/exampleFromFile.py | python -m examples.exampleFromFile --a -  --b examples/__pycache__/exampleFromFile.cpython-37.pyc
    '''
