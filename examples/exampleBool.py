def add(a: bool=True, b: bool=False):
    '''
    @param a: first bool
    @param b: second bool
    '''
    print(a, b)
    return a or b

if __name__ == "__main__":
    from argParseFromDoc import get_parser_from_function
    parser = get_parser_from_function(add)
    args = parser.parse_args()
    print(add(**vars(args)))