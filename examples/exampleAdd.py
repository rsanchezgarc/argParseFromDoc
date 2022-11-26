def add(a: int, b: int):
    '''
    @param a: first number
    @param b: second number
    '''
    return a + b

if __name__ == "__main__":
    from argParseFromDoc import parse_function_and_call
    out = parse_function_and_call(add)
    print(out)