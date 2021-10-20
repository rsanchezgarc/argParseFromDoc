def add(a: int, b: int):
    '''
    @param a: first number
    @param b: second number
    '''
    return a + b

if __name__ == "__main__":
    from argParseFromDoc import get_parser_from_function
    from argparse import ArgumentParser
    parser = ArgumentParser(prog="Add_example")
    parser.add_argument("--other_type_of_argument", type=str, default="Not provided")
    ### If you prefer a group instead of a whole parser
    # group = parser.add_argument_group()
    # get_parser_from_function(add, parser=group)
    get_parser_from_function(add, parser=parser)
    args = parser.parse_args()
    print(add(**vars(args)))