import os
import tempfile
import subprocess
import inspect
import textwrap
from typing import List, Optional, TextIO, Tuple, Literal
from unittest import TestCase
from pathlib import Path

from argParseFromDoc.commandStrGenerator import generate_command_for_argparseFromDoc


class TestCommandExecution(TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.tempdir):
            import shutil
            shutil.rmtree(self.tempdir)

    def create_test_script(self, func):
        """Creates a test script with parse_function_and_call"""
        script_path = os.path.join(self.tempdir, f"{func.__name__}.py")

        # Get the source and dedent it
        source = inspect.getsource(func)
        source = textwrap.dedent(source)

        script_content = f'''from typing import List, Optional, TextIO, Tuple, Literal

{source}

if __name__ == "__main__":
    from argParseFromDoc import parse_function_and_call
    result = parse_function_and_call({func.__name__})
    print(result)
'''
        with open(script_path, 'w') as f:
            f.write(script_content)
        return script_path

    def test_simple_addition(self):
        def add(a: int, b: int = 10):
            """
            Add two numbers
            @param a: First number
            @param b: Second number (default: 10)
            """
            return a + b

        script_path = self.create_test_script(add)

        # Test with both arguments
        cmd = generate_command_for_argparseFromDoc(script_path, add, a=5, b=3)
        result = subprocess.check_output(cmd.split(), text=True)
        self.assertEqual(int(result.strip()), 8)

        # Test with default value
        cmd = generate_command_for_argparseFromDoc(script_path, add, a=5)
        result = subprocess.check_output(cmd.split(), text=True)
        self.assertEqual(int(result.strip()), 15)

    def test_list_handling(self):
        def sum_list(numbers: List[float]):
            """
            Sum a list of numbers
            @param numbers: List of numbers to sum
            """
            return sum(numbers)

        script_path = self.create_test_script(sum_list)

        cmd = generate_command_for_argparseFromDoc(
            script_path,
            sum_list,
            numbers=[1.5, 2.5, 3.0]
        )
        result = subprocess.check_output(cmd.split(), text=True)
        self.assertEqual(float(result.strip()), 7.0)

    def test_module_mode(self):
        def simple_func(x: int):
            """
            @param x: A number
            """
            return x * 2

        # Create a package structure
        pkg_dir = os.path.join(self.tempdir, "testpkg")
        os.makedirs(pkg_dir)
        with open(os.path.join(pkg_dir, "__init__.py"), "w") as f:
            pass

        script_path = os.path.join(pkg_dir, "main.py")
        with open(script_path, "w") as f:
            source = textwrap.dedent(inspect.getsource(simple_func))
            f.write(f'''from typing import List, Optional

{source}

if __name__ == "__main__":
    from argParseFromDoc import parse_function_and_call
    result = parse_function_and_call(simple_func)
    print(result)
''')

        # Test module execution
        cmd = generate_command_for_argparseFromDoc(
            "testpkg.main",
            simple_func,
            use_module=True,
            x=5
        )

        # Set up environment with correct PYTHONPATH
        env = os.environ.copy()
        env['PYTHONPATH'] = self.tempdir + os.pathsep + env.get('PYTHONPATH', '')

        result = subprocess.check_output(
            cmd.split(),
            text=True,
            env=env
        )
        self.assertEqual(int(result.strip()), 10)

    def test_custom_python(self):
        def simple_add(x: int):
            """
            @param x: A number
            """
            return x + 1

        script_path = self.create_test_script(simple_add)

        import sys
        # Test with custom python executable
        cmd = generate_command_for_argparseFromDoc(
            script_path,
            simple_add,
            python_executable=sys.executable,
            x=5
        )
        result = subprocess.check_output(cmd.split(), text=True)
        self.assertEqual(int(result.strip()), 6)


    def test_boolean_combinations(self):
        def bool_combo(
                flag1: bool = False,  # default False, should use --flag1
                flag2: bool = True,  # default True, should use --NOT_flag2
                flag3: bool = False,  # testing multiple False defaults
                flag4: bool = True  # testing multiple True defaults
        ):
            """
            Test various boolean flag combinations
            @param flag1: First flag (default: False)
            @param flag2: Second flag (default: True)
            @param flag3: Third flag (default: False)
            @param flag4: Fourth flag (default: True)
            """
            return str({
                "flag1": flag1,
                "flag2": flag2,
                "flag3": flag3,
                "flag4": flag4
            })

        script_path = self.create_test_script(bool_combo)

        # Test all defaults (should generate no args)
        cmd = generate_command_for_argparseFromDoc(script_path, bool_combo)
        result = eval(subprocess.check_output(cmd.split(), text=True))
        self.assertFalse(result["flag1"])
        self.assertTrue(result["flag2"])
        self.assertFalse(result["flag3"])
        self.assertTrue(result["flag4"])

        kwargs = dict(
            flag1=True,
            flag2=False,
            flag3=False,
            flag4=True
        )
        # Test setting all flags opposite to their defaults
        cmd = generate_command_for_argparseFromDoc(
            script_path,
            bool_combo,
            **kwargs
        )
        print(cmd)
        result = eval(subprocess.check_output(cmd.split(), text=True))
        self.assertTrue(result["flag1"] == kwargs["flag1"])
        self.assertTrue(result["flag2"] == kwargs["flag2"])
        self.assertTrue(result["flag3"] == kwargs["flag3"])
        self.assertTrue(result["flag4"] == kwargs["flag4"])

        kwargs = dict(
            flag1=True,  # change False → True
            flag2=True,  # keep True
            flag3=False,  # keep False
            flag4=False  # change True → False
        )
        # Test mixed combinations
        cmd = generate_command_for_argparseFromDoc(
            script_path,
            bool_combo,
            **kwargs
        )
        result = eval(subprocess.check_output(cmd.split(), text=True))
        self.assertTrue(result["flag1"] == kwargs["flag1"])
        self.assertTrue(result["flag2"] == kwargs["flag2"])
        self.assertTrue(result["flag3"] == kwargs["flag3"])
        self.assertTrue(result["flag4"] == kwargs["flag4"])

    def test_list_complex(self):
        def list_handler(
                ints: List[int],  # basic int list
                opt_floats: Optional[List[float]] = None,  # optional float list
                strs: List[str] = ["default"],  # list with default
                single_int: List[int] = [42],  # single-item default
                empty_list: List[str] = []  # empty default
        ):
            """
            Test various list configurations
            @param ints: List of integers
            @param opt_floats: Optional list of floats
            @param strs: List of strings with default
            @param single_int: List with single integer
            @param empty_list: Empty list of strings
            """
            return str({
                "ints": ints,
                "opt_floats": opt_floats,
                "strs": strs,
                "single_int": single_int,
                "empty_list": empty_list
            })

        script_path = self.create_test_script(list_handler)

        # Test with only required arguments
        cmd = generate_command_for_argparseFromDoc(
            script_path,
            list_handler,
            ints=[1, 2, 3]
        )
        result = eval(subprocess.check_output(cmd.split(), text=True))
        self.assertEqual(result["ints"], [1, 2, 3])
        self.assertIsNone(result["opt_floats"])
        self.assertEqual(result["strs"], ["default"])
        self.assertEqual(result["single_int"], [42])
        self.assertEqual(result["empty_list"], [])

        # Test with all arguments specified
        cmd = generate_command_for_argparseFromDoc(
            script_path,
            list_handler,
            ints=[1, 2, 3],
            opt_floats=[1.5, 2.5],
            strs=["hello", "world"],
            single_int=[99],
            empty_list=["not", "empty", "anymore"]
        )
        result = eval(subprocess.check_output(cmd.split(), text=True))
        self.assertEqual(result["ints"], [1, 2, 3])
        self.assertEqual(result["opt_floats"], [1.5, 2.5])
        self.assertEqual(result["strs"], ["hello", "world"])
        self.assertEqual(result["single_int"], [99])
        self.assertEqual(result["empty_list"], ["not", "empty", "anymore"])


    def test_list_with_spaces(self):
        def space_handler(strings: List[str]):
            """
            Test handling of strings with spaces in a list
            @param strings: List of strings that might contain spaces
            """
            return str(strings)

        script_path = self.create_test_script(space_handler)

        cmd = generate_command_for_argparseFromDoc(
            script_path,
            space_handler,
            strings=["'hello world'", "'contains spaces'", "'no-spaces'"]
        )
        result = subprocess.check_output(cmd, text=True, shell=True).strip()
        self.assertEqual(
            result,
            "['hello world', 'contains spaces', 'no-spaces']"
        )


    def test_empty_lists(self):
        def empty_handler(
                required_list: List[int],
                optional_list: Optional[List[float]] = None,
        ):
            """
            Test handling of empty lists
            @param required_list: Required list that could be empty
            @param optional_list: Optional list that could be empty
            """
            return str({
                "required_list": required_list,
                "optional_list": optional_list,
            })

        script_path = self.create_test_script(empty_handler)

        # Test with empty required list
        cmd = generate_command_for_argparseFromDoc(
            script_path,
            empty_handler,
            required_list=[1]
        )
        result = eval(subprocess.check_output(cmd.split(), text=True))
        self.assertEqual(result["required_list"], [1])
        self.assertIsNone(result["optional_list"])

        # Test with empty optional list
        cmd = generate_command_for_argparseFromDoc(
            script_path,
            empty_handler,
            required_list=[1],
            optional_list=[2.],
        )
        print(cmd)
        result = eval(subprocess.check_output(cmd.split(), text=True))
        self.assertEqual(result["required_list"], [1])
        self.assertEqual(result["optional_list"], [2.])

        cmd = generate_command_for_argparseFromDoc(
            script_path,
            empty_handler,
            required_list=[1],
            optional_list=[2., 3.],
        )
        print(cmd)
        result = eval(subprocess.check_output(cmd.split(), text=True))
        self.assertEqual(result["required_list"], [1])
        self.assertEqual(result["optional_list"], [2., 3.])

if __name__ == '__main__':
    import unittest

    unittest.main()