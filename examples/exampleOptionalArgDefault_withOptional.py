from typing import Optional


def fun(a: int, b: Optional[int] = None):
    '''
    @param a: first number
    @param b: optional argument
    '''
    return a if b is None  else a+b

if __name__ == "__main__":

    from argParseFromDoc import parse_function_and_call
    out = parse_function_and_call(fun)
    print(out)

"""
python -m examples.exampleOptionalArgDefault_withOptional --a 3
python -m examples.exampleOptionalArgDefault_withOptional --a 3 --b 4

"""