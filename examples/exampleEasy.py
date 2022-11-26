def hello(a: str):
    '''
    @param a: a message
    '''
    return a

if __name__ == "__main__":
    from argParseFromDoc import parse_function_and_call
    out = parse_function_and_call(hello)
    print(out)