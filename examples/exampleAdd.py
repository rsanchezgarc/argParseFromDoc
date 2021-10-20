def add(a: int, b: int):
    '''
    @param a: first number
    @param b: second number
    '''
    return a + b

if __name__ == "__main__":
    from argParseFromDoc import get_parser_from_function
    parser = get_parser_from_function(add)
    args = parser.parse_args()
    print(add(**vars(args)))