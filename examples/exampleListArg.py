from typing import List

def addList(several_nums: List[int], b: int=1):
    '''
    @param several_nums: first number
    @param b: second number
    '''
    return [a + b for a in several_nums]

if __name__ == "__main__":
    from argParseFromDoc import parse_function_and_call
    out = parse_function_and_call(addList)
    print(out)