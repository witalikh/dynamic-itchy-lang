from src.interpreter import Interpreter

import argparse
import sys


def main():
    # TODO: REPL
    arg_parser = argparse.ArgumentParser(
        prog='Dynamic Itchy Interpreter v1.0',
        description='Execute Dynamic Itchy source code files from CLI, and write results into stdout'
    )

    arg_parser.add_argument(
        '-i', '--input',
        action='append',
        help='Specify input file(s) for source code.\n'
             'This option can be used multiple time to combine different source code files into one,'
             'evaluation of which is in order, specified here.\n'
             'Example: -i file_1 -i file_2 ... It executes file_1 first, then file_2',

    )

    arg_parser.add_argument(
        '-o', '--output',
        help='Specify the output file to write the execution results. \n'
             'If not specified, it will be printed to the console.'
    )

    arg_parser.add_argument(
        '--no-output',
        action='store_true',
        help='Explicitly indicate to not print the results to the console or any file.'
    )

    args = arg_parser.parse_args()

    src_to_exec = []
    for input_file in args.input:
        with open(input_file, 'r') as f:
            src_to_exec.append(f.read())

    interpreter = Interpreter()
    for src in src_to_exec:
        interpreter.execute(src)

    if args.no_output:
        pass

    elif not args.output:
        print(interpreter.result)

    else:
        with open(args.output, 'w') as f:
            f.write(interpreter.result)


if __name__ == '__main__':
    main()
