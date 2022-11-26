def add(a: bool=True, b: bool=False):
    '''
    @param a: first bool
    @param b: second bool
    '''
    return a or b

if __name__ == "__main__":
    from argParseFromDoc import parse_function_and_call
    out = parse_function_and_call(add)
    print(out)