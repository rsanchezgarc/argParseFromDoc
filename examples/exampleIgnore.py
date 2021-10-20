def manyArgsFun(a: int, b: int, c: int = 1, d: int = 2, e: str = "oneStr"):
    '''

    :param a: a
    :param b: b
    :param c: c
    :param d: d
    :param e: e
    :return:
    '''
    print(e)
    return sum([a, b, c, d])


if __name__ == "__main__":
    from argParseFromDoc import get_parser_from_function
    # parser = get_parser_from_function(manyArgsFun, args_to_ignore=["c", "d", "e"])
    parser = get_parser_from_function(manyArgsFun, args_to_include=["a", "b"])
    args = parser.parse_args()
    print(manyArgsFun(**vars(args)))
