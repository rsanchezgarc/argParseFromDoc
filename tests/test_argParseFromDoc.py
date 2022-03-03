import tempfile
from io import StringIO
from typing import Tuple, List, Dict, TextIO
from unittest import TestCase

from argParseFromDoc import AutoArgumentParser
from argParseFromDoc.argParseFromDoc import get_parser_from_function


class Test(TestCase):

    def _check_help(self, help_str, to_check_list):
        for substr in to_check_list:
            assert substr in help_str, "Error, '%s' not in '%s'"%(substr, help_str)

    def test_get_parser_tuple(self):
        def fun1(a: int, ns: Tuple[int] = (1,2))-> List[int]:
            '''
            :param a: input to add
            :param ns: input param iterable
            :return: an int
            '''
            return [a +elem for elem in ns ]

        parser = get_parser_from_function(fun1)

        with StringIO() as strFile:
            parser.print_help(strFile)
            strFile.seek(0)
            self._check_help( strFile.read(), ["  --a A             input to add Default=None",
                                               "  --ns NS [NS ...]  input param iterable Default=(1, 2)"])

        args = parser.parse_args(["--a", "1", "--ns", "0", "-1" ])
        result = fun1( ** vars(args))
        self.assertTrue( result == [1,0] )

    def test_get_parser_str(self):
        def fun1(a: str, ns: Tuple[str] = ("1", "2"))-> List[str]:
            '''
            :param a: input to add
            :param ns: input param iterable
            :return: an int
            '''
            return [a +elem for elem in ns ]

        parser = get_parser_from_function(fun1)

        with StringIO() as strFile:
            parser.print_help(strFile)
            strFile.seek(0)
            self._check_help( strFile.read(), ["  --a A             input to add Default=None",
                                               "  --ns NS [NS ...]  input param iterable Default=('1', '2')"])

        args = parser.parse_args(["--a", "1", "--ns", "0", "-1" ])
        result = fun1( ** vars(args))
        self.assertTrue( result == ["10", "1-1"] )

    def test_get_parser_file(self):
        def fun1(a: TextIO)-> int:
            '''
            :param a: a text file
            :return: number of lines
            '''
            return len( a.readlines())

        parser = get_parser_from_function(fun1)

        with tempfile.NamedTemporaryFile(mode="w", delete=True) as inputFile:
            inputFile.write(("Hola\n"*4))
            inputFile.seek(0)
            args = parser.parse_args(["--a", inputFile.name ])
            result = fun1( ** vars(args))

        self.assertTrue( result == 4 )

    def test_boolean_defaultTrue(self):
        def fun1(a: int, b: bool = True)-> bool:
            '''
            :param a: input 1
            :param b: input bool
            :return: an int
            '''
            return bool(a) & b

        parser = get_parser_from_function(fun1)
        with StringIO() as strFile:
            parser.print_help(strFile)
            strFile.seek(0)
            # print(strFile.read()); strFile.seek(0)
            self._check_help( strFile.read(), ["  --a A       input 1 Default=None",
                                               "  --NOT_b     input bool Action: store_false for variable b"])

        args = parser.parse_args(["--a", "1", "--NOT_b" ])
        result = fun1( ** vars(args))
        self.assertTrue( result == False)

        args = parser.parse_args(["--a", "1" ])
        result = fun1( ** vars(args))
        self.assertTrue( result == True)

    def test_boolean_defaultFalse(self):
        def fun1(a: int, b: bool = False)-> bool:
            '''
            :param a: input 1
            :param b: input bool
            :return: an int
            '''
            return bool(a) & b

        parser = get_parser_from_function(fun1)
        with StringIO() as strFile:
            parser.print_help(strFile)
            strFile.seek(0)
            self._check_help( strFile.read(), ["  --a A       input 1 Default=None",
                                               "  --b         input bool Action: store_true for variable b"])

        args = parser.parse_args(["--a", "1", "--b" ])
        result = fun1( ** vars(args))
        self.assertTrue( result == True)

        args = parser.parse_args(["--a", "0", "--b" ])
        result = fun1( ** vars(args))
        self.assertTrue( result == False)

        args = parser.parse_args(["--a", "1" ])
        result = fun1( ** vars(args))
        self.assertTrue( result == False)


    def test_get_parser_kwargs(self):
        def fun1(a: int, b: bool = False, *args, **kwargs)-> bool:
            '''
            :param a: input 1
            :param b: input bool
            :return: an int
            '''
            return bool(a) & b

        parser = get_parser_from_function(fun1)

        parser = get_parser_from_function(fun1)
        with StringIO() as strFile:
            parser.print_help(strFile)
            strFile.seek(0)
            self._check_help( strFile.read(), ["  --a A       input 1 Default=None",
                                               "  --b         input bool Action: store_true for variable b"])

        args = parser.parse_args(["--a", "1", "--b" ])
        result = fun1( ** vars(args))
        self.assertTrue( result == True)

        args = parser.parse_args(["--a", "0", "--b" ])
        result = fun1( ** vars(args))
        self.assertTrue( result == False)

        args = parser.parse_args(["--a", "1" ])
        result = fun1( ** vars(args))
        self.assertTrue( result == False)


    def test_get_parser_class(self):
        class Adder():
            def __init__(self, to_add: int, **kwargs):
                '''
                :param to_add: the parameter to add
                '''

                self.to_add = to_add

            def add(self, b: int, **kwargs):
                '''
                :param b: number to be added
                '''
                return self.to_add + b

        parser = get_parser_from_function(Adder.__init__)
        get_parser_from_function(Adder.add, parser=parser)
        args = vars(parser.parse_args(["--b", "2", "--to_add", "1" ]))
        adder = Adder(**args)
        result = adder.add(**args)

        self.assertTrue( result == 3 )


    def test_get_parser_duplicated_arg(self):
        def fun1(a: str, ns: int, x: int)-> int:
            '''
            :param a: input to add
            :param ns: input param iterable
            :param ns: duplicated
            :return: an int
            '''
            return 1

        self.assertRaises(AssertionError, get_parser_from_function, fun1)

    def test_get_parser_mismatch_docu_typing(self):
        def fun1(a: str, ns: int, x: int)-> int:
            '''
            :param a: input to add
            :param ns: input param iterable
            :return: an int
            '''
            return 1

        self.assertRaises(AssertionError, get_parser_from_function, fun1)

    def test_get_parser_mismatch_typing_docu(self):
        def fun1(a: str, ns: int)-> int:
            '''
            :param a: input to add
            :param ns: input param iterable
            :param ns: MISMATCHED
            :return: an int
            '''
            return 1

        self.assertRaises(AssertionError, get_parser_from_function, fun1)

    def test_get_parser_mismatch_typing_docu_2(self):
        def fun1(a: int, b: bool = True)-> int:
            '''
            :param a: input to add
            :param ns: input  bool
            :return: an int
            '''
            return bool(a) & b

        self.assertRaises(AssertionError, get_parser_from_function, fun1)

    def test_get_parser_mismatch_typing_docu_3(self):
        def fun1(a: int, b: bool = True)-> int:
            '''
            :param b: input 1
            :param a: input  2
            :return: an int
            '''
            return bool(a) & b

        self.assertRaises(AssertionError, get_parser_from_function, fun1)

    def test_get_parser_nonSupportedType_1(self):
        def fun1(a: str, ns: Dict[str, str] = None)-> List[str]:
            '''
            :param a: input to add
            :param ns: input param iterable
            :return: an int
            '''
            return [a +elem for elem in ns.keys() ]

        self.assertRaises(AssertionError, get_parser_from_function, fun1)

    def test_get_parser_nonSupportedType_2(self):
        def fun1(a: str, ns: List[List[str]] = None)-> List[str]:
            '''
            :param a: input to add
            :param ns: input param iterable
            :return: an int
            '''
            return [[a] +elem for elem in ns ]

        self.assertRaises(AssertionError, get_parser_from_function, fun1)

    def test_get_parser_nonSupportedType_3(self):
        def fun1(a: str, ns: StringIO = None)-> str:
            '''
            :param a: input to add
            :param ns: input param iterable
            :return: an int
            '''
            return a

        self.assertRaises(ValueError, get_parser_from_function, fun1)

    def test_argumentNoneAndOptional(self):
        def fun(a: int, b: int = None):
            '''
            @param a: first number
            @param b: optional argument
            '''
            return a if b is None else a + b

        parser = get_parser_from_function(fun, args_optional=["b"])
        args = vars(parser.parse_args(["--a", "1" ]))
        result = fun(**args)
        self.assertEqual(result, 1)

        args = vars(parser.parse_args(["--a", "1", "--b", "2" ]))
        result = fun(**args)
        self.assertEqual(result, 3)

    # def test_Literal_as_Choice(self): #TODO: Implement litaral for python 3.8+
    #     def fun( msg : Literal["hola", "adios"]):
    #         '''
    #         @param a: a predefined option message
    #         @param b: optional argument
    #         '''
    #         return msg
    #
    #     parser = get_parser_from_function(fun)
    #     args = vars(parser.parse_args(["--a", "1" ]))
    #     result = fun(**args)
    #     self.assertEqual(result, 1)
    #
    #     args = vars(parser.parse_args(["--a", "1", "--b", "2" ]))
    #     result = fun(**args)
    #     self.assertEqual(result, 3)

    def test_ignoreArgs(self):
        def fun(a: int, b: int = 1, c:Exception =None):
            '''
            @param a: first number
            @param b: second number
            @param c: c is an optional argument to be ignored. Exception is not supported by argParseFromDocs
            '''
            return a if b is None else a + b

        parser = get_parser_from_function(fun, args_to_ignore=["c"])
        # parser.print_help()
        args = vars(parser.parse_args(["--a", "1" ]))
        result = fun(**args)
        self.assertEqual(result, 2)

        args = vars(parser.parse_args(["--a", "1", "--b", "2" ]))
        result = fun(**args)
        self.assertEqual(result, 3)

    def test_AutoArgumentParser1(self):
        parser = AutoArgumentParser()
        parser.add_argument("--a", type=int)
        group = parser.add_argument_group(title="g")
        group.add_argument("--g1", type=int, default=-1)
        args = parser.parse_args_groups(["--a", "1"])
        self.assertEqual(args["g"].g1, -1)

    def test_AutoArgumentParser2(self):

        def fun(a: int, b: int = None):
            '''
            @param a: first number
            @param b: optional argument
            '''
            return a if b is None else a + b

        parser = AutoArgumentParser()
        parser.add_argument("--main", type=int)
        group = parser.add_argument_group(title="g")
        group.add_argument("--g1", type=int, default=-1)
        parser.add_args_from_function(fun)
        parser.print_help()
        pars1 =  parser.parse_args(["--a", "1", "--b", "2"])
        pars2 =  parser.parse_args_groups(["--a", "1", "--b", "2"])
        self.assertEqual(pars1.g1, pars2["g"].g1)
