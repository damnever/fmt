# -*- coding: utf-8 -*-

from __future__ import absolute_import

import ast
import string
import sys
import re
from functools import partial


class Fmt(object):

    def __init__(self):
        self._g_ns = {}

    def register(self, name, value, update=False):
        if not update and name in self._g_ns:
            raise ValueError('namespace "{}" already registered'.format(name))
        self._g_ns[name] = value

    def mregister(self, ns, update=False):
        for k, v in ns.items():
            self.register(k, v, update)

    def __call__(self, f_str, *_args):
        frame = sys._getframe(1)
        # locals will cover globals
        ns = self._g_ns
        ns.update(frame.f_globals)
        ns.update(frame.f_locals)

        try:
            nodes = Parser(f_str).parse()
        except Reader.EOF:
            raise SyntaxError('f-strings is not complete.')

        return Render.generate(nodes, ns)


class Reader(object):

    class EOF(Exception):
        pass

    def __init__(self, f_str):
        self._f_str = f_str
        self._next_pos = 0
        self._length = len(f_str)

    @property
    def pos(self):
        return self._next_pos

    def read_util(self, ch):
        self._check_eof()
        end_pos = self._f_str.find(ch, self._next_pos)
        if end_pos < 0:
            return None
        value = self._f_str[self._next_pos: end_pos]
        self._next_pos = end_pos
        return value

    def read(self, n=1):
        self._check_eof()
        end_pos = self._next_pos + n
        value = self._f_str[self._next_pos: end_pos]
        self._next_pos = end_pos
        return value

    def peek(self, offset=0):
        pos = self._next_pos+offset
        self._check_eof(pos)
        return self._f_str[pos]

    def rest(self, start):
        return self._f_str[start:]

    def remains(self):
        return self._length - self._next_pos

    def is_eof(self):
        return self._next_pos >= self._length

    def _check_eof(self, pos=None):
        if self.is_eof() or (pos and pos >= self._length):
            raise self.EOF()



class Node(object):
    def generate(self, ns):
        raise NotImplemented()


class Text(Node):
    def __init__(self, content):
        self._content = content

    def generate(self, _namespace):
        return self._content


class Constant(Node):
    def __init__(self, name, fmt):
        self._name = name
        self._fmt = fmt

    def generate(self, namespace):
        name = self._name
        value = namespace.get(name, None)
        if value is None:
            raise NameError(
                '"{}" cannot be found in any namespace.'.format(name))
        return self._fmt.format(**{name: value})


class Expression(Node):
    def __init__(self, expr, fmt, name='name'):
        self._expr = expr
        self._name = name
        self._fmt = fmt.replace(expr, name).replace(' ', '')

    def generate(self, namespace):
        ns = {}
        try:
            exec('{}={}'.format(self._name, self._expr), namespace.copy(), ns)
        except NameError as e:
            name = e.args[0].split("'", 3)[1]
            raise NameError(
                '"{}" cannot be found in any namespace.'.format(name))
        return self._fmt.format(**ns)


class Parser(object):
    _ast_parse = partial(ast.parse, filename='<f-strings>', mode='eval')

    def __init__(self, f_str):
        self._reader = Reader(f_str)

    def parse(self):
        reader = self._reader
        nodes = []

        while not reader.is_eof():
            # text
            value = reader.read_util('{')
            if value is None:
                raise SyntaxError(
                    'expect "{" after position {}'.format(reader.pos))
            nodes.append(Text(value))
            reader.read()

            # one or more {
            braces, is_comp, skip = self._parse_escape()
            if skip:
                nodes.append(Text('{' * ((braces+1) >> 1)))
                continue
            else:
                nodes.append(Text('{' * (braces >> 1)))

            # placeholders
            node_str = reader.read_util('}')
            if node_str is None:
                raise SyntaxError(
                    'expect "}" after position {}'.format(reader.pos))
            if is_comp:
                node_str = '{' + node_str + '}'
            node = self._parse_node(node_str)
            nodes.append(node)

            # one or more }
            if braces > 1:
                nodes.append(Text('}' * (braces >> 1)))
            if is_comp:
                braces += 1

            need_more = braces - reader.remains()
            if need_more > 0:
                raise SyntaxError(
                    'need {} of "}}" character(s) as position {}'.format(
                        need_more, reader.pos)
                )
            reader.read(braces)

        return nodes

    def _parse_escape(self, _mbp=re.compile(r"\s+?\{", re.S)):
        reader = self._reader
        braces, is_comp, skip = 1, False, False

        if reader.peek() == '{':
            braces += 1
            while 1:
                if reader.peek(braces-1) != '{':
                    break
                braces += 1

            reader.read(braces-1)
            if braces % 2 == 0:
                if _mbp.match(reader.rest(reader.pos)) is not None:
                    skip = True
                else:  # assume the next is dict/ comprehensions
                    is_comp = True
                    braces -= 1

        return braces, is_comp, skip

    def _parse_node(self, node_str, _table=string.maketrans('\n\r\t', ' '*3)):
        node_str = node_str.strip().translate(_table)
        fmt = '{{{}}}'.format(node_str)

        expr = self._parse_node_str(node_str)
        ast_node = self._ast_parse(expr)
        if ast_node.body.__class__.__name__ == 'Name':
            return Constant(expr, fmt)
        else:
            return Expression(expr, fmt)

    def _parse_node_str(self, node_str, _cvss=('s', 'r', 'a')):
        # f-string: '''... <text> {
        #   <expression>
        #   <optional !s, !r, or !a>
        #   <optional : format specifier>
        # } <text> ...'''
        expr = None
        pos = self._reader.pos

        splitd = node_str.rsplit(':', 1)
        if len(splitd) > 1:
            left, fmt_spec = splitd
            if not fmt_spec:
                raise SyntaxError(
                    'need format specifier after ":"'
                    ' at position {}'.format(pos + len(left))
                )
            elif ')' in fmt_spec or '}' in fmt_spec or 'lambda' in left:
                left = node_str
        else:
            left = splitd[0]

        splitd = left.rsplit('!', 1)
        if len(splitd) > 1:
            expr, cvs_spec = splitd
            if cvs_spec not in _cvss:
                raise SyntaxError(
                    'optional conversions must be one of'
                    ' {} at {}'.format(_cvss, pos + len(expr))
                )
        else:
            expr = splitd[0]

        return expr.strip()


class Render(object):

    @classmethod
    def generate(cls, nodes, namespace):
        contents = []

        for node in nodes:
            contents.append(node.generate(namespace))

        return ''.join(contents)
