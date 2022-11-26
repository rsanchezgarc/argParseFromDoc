
if __name__ == "__main__":

    from typing import Literal

    def fun(a: str, b: Literal["abc", "cde"]):
        '''
        @param a: first number
        @param b: optional argument
        '''
        return a if b is None else a + b

    from argParseFromDoc import parse_function_and_call
    out = parse_function_and_call(fun)
    print(out)