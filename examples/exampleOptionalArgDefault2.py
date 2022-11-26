def fun(a: int, b: int = None):
    '''
    @param a: first number
    @param b: optional argument
    '''
    return a if b is None  else a+b

if __name__ == "__main__":
    from argParseFromDoc import get_parser_from_function

    parser = get_parser_from_function(fun, args_optional=["b"])
    args = parser.parse_args()
    print(fun(**vars(args)))