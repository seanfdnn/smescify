#!/usr/bin/env python3
import click
import more_itertools
import textwrap


@click.command()
@click.argument('input', type=click.File('r'))
def parse(input):
    # What convention this document uses for an indent level,
    # i.e. 2 or 4 spaces. This is inferred from the document
    parser = Parser(input)
    paras = parser.parse()
    lines = list([line for para in paras for line in parse_para(para, uppercase_header=True)])

    body = '\n\n'.join(lines)
    print(body)


def parse_para(para, level=0, leader='', show_formatting=False, uppercase_header=False):
    text = ' ' * 6 * (level - 1)
    text += leader
    if para.header:
        header = para.header
        if uppercase_header:
            header = header.upper()
        if show_formatting:
            text += '\033[4m' + header + '\033[0m. '
        else:
            text += header + '. '

    text += para.inline_text
    yield text

    for idx, subpara in enumerate(para.sub_paras):
        leader = get_leader(idx, level + 1)
        for line in list([line for line in parse_para(subpara, level + 1, leader, show_formatting=show_formatting)]):
            yield line


def get_leader(index, level):
    alphas = 'abcdefghiktlmnopqrstuvwzyz'
    leader = ''
    if level == 1:
        leader = str(index + 1) + '. '
    elif level == 2:
        leader = alphas[index] + '. '
    elif level == 3:
        leader = '(' + str(index + 1) + ')'
    elif level == 4:
        leader = '(' + alphas[index] + ')'

    return leader.ljust(6)

class Paragraph:
    def __init__(self, inline_text, header=None):
        self.header = header
        self.inline_text = inline_text
        self.sub_paras = []


class Parser:
    def __init__(self,input):
        self.indent_size = None
        self.input = more_itertools.peekable(input)
        self.line_number = 0

    def parse(self):
        return list(self.parse_nested(0))

    def parse_nested(self, current_indent_level):
        while self.input.peek():
            line = self.input.peek()
            self.line_number += 1

            # Ignore whitespace lines entirely
            if line.isspace():
                next(self.input)
                continue

            # Calculate the indentation of the line
            indent_level = self._calc_indent(line, current_indent_level)

            line = line.lstrip().rstrip()
            sub_paras = []

            if indent_level == current_indent_level:
                # Consume the line
                next(self.input)

                header = None
                if ':' in line:
                    splitline = line.split(':',1)
                    header = splitline[0].lstrip().rstrip()
                    line = splitline[1]
                para = Paragraph(line.lstrip().rstrip(), header)
                para.sub_paras = list(self.parse_nested(indent_level + 1))
                yield para

            elif indent_level < current_indent_level:
                return

    def _calc_indent(self, line, current_indent_level):
        indent_spaces = count_leading_spaces(line)
        if not self.indent_size and indent_spaces > 0:
            self.indent_size = indent_spaces

        if self.indent_size:
            if indent_spaces % self.indent_size > 0:
                raise Exception(f'Irregular indent on line {self.line_number}: {line}, expected {self.indent_size * current_indent_level} but got {indent_spaces}')
            indent_level = indent_spaces // self.indent_size
        else:
            indent_level = 0

        if (indent_level - current_indent_level) > 1:
            raise Exception(f'Unexpected indent on line {self.line_number}: {line}')
        return indent_level

def count_leading_spaces(string):
    return len(string) - len(string.lstrip())


if __name__ == '__main__':
    parse()
