
class Adder():
    def __init__(self, to_add: int, **kwargs):
        '''
        :param to_add: the parameter to add
        '''

        self.to_add = to_add

    def add( self, b: int, **kwargs):
        '''
        :param b: number to be added
        '''
        return self.to_add + b

if __name__ == "__main__":
    from argParseFromDoc import get_parser_from_function

    parser = get_parser_from_function(Adder.__init__)
    get_parser_from_function(Adder.add, parser= parser)
    args = vars(parser.parse_args())
    adder = Adder(**args)
    print( adder.add(**args))
