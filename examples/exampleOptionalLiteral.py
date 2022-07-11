
if __name__ == "__main__":
    from argParseFromDoc import get_parser_from_function

    from typing import Literal, Optional

    def fun(a: str, b: Optional[Literal["abc", "cde"]]):
        '''
        @param a: first number
        @param b: optional argument
        '''
        return a if b is None else a + b

    parser = get_parser_from_function(fun)
    args = parser.parse_args()
    print(fun(**vars(args)))