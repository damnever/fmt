# -*- coding: utf-8 -*-

from __future__ import absolute_import

import re
import ast
import string
import sys
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

        nodes = Parser(f_str).parse()
        return generate(nodes, ns)


def generate(nodes, namespace):
    contents = []

    for node in nodes:
        contents.append(node.generate(namespace))

    return ''.join(contents)


class Node(object):
    def generate(self, ns):
        raise NotImplemented()


class Text(Node):
    def __init__(self, *contents):
        self._content = ''.join(contents)

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
            print('{}={}'.format(self._name, self._expr))
            exec('{}={}'.format(self._name, self._expr), namespace.copy(), ns)
        except NameError as e:
            name = e.args[0].split("'", 3)[1]
            raise NameError(
                '"{}" cannot be found in any namespace.'.format(name))
        return self._fmt.format(**ns)


class Parser(object):
    _PATTERN_SPEC = re.compile(
        r"""
        (?P<ltext>[^\{]*)
        (?P<lbrace>\{)?
            (?P<lbraces>(?(lbrace)[\s\{]*))
        (?P<mtext>[^\{\}]*)
        (?P<rbrace>\})?
            (?P<rbraces>(?(rbrace)[\s\}]*))
        (?P<rtext>[^\{]*)
        """, re.S|re.X|re.M
    )
    _PATTERN_COMP = re.compile(r'\w\s+for\s+\w\s+in\s+.+', re.S|re.X|re.M)
    _ast_parse = partial(ast.parse, filename='<f-strings>', mode='eval')

    def __init__(self, f_str):
        self._f_str = f_str

    def parse(self, _pattern=_PATTERN_SPEC):
        if self._f_str.isspace():
            return self._f_str

        nodes = []

        for match_obj in _pattern.finditer(self._f_str):
            groups = match_obj.groupdict()
            ltext = groups['ltext'] or ''
            lbraces = (groups['lbrace'] or '') + (groups['lbraces'] or '')
            mtext = (groups['mtext'] or '')
            rbraces = (groups['rbrace'] or '') + (groups['rbraces'] or '')
            rtext = groups['rtext'] or ''
            if lbraces:
                raw, lbraces = lbraces, lbraces.rstrip()
                mtext = ' ' * (len(raw)-len(lbraces)) + mtext
            if rbraces:
                raw, rbraces = rbraces, rbraces.rstrip()
                rtext = ' ' * (len(raw)-len(rbraces)) + rtext

            if not lbraces and not rbraces:
                nodes.append(Text(ltext, mtext, rtext))
                continue

            if ltext:
                nodes.append(Text(ltext))

            lb_num, rb_num = lbraces.count('{'), rbraces.count('}')
            if mtext.isspace() or not (lbraces and rbraces):
                if lbraces:
                    self._check_braces(lbraces, True, '{')
                if rbraces:
                    self._check_braces(rbraces, True, '}')
                nodes.append(Text('{' * (lb_num>>1), mtext, '}' * (rb_num>>1)))
                continue

            is_comp = self._is_dict_or_set_comp(mtext)
            if is_comp:
                self._check_braces(lbraces, True, '{')
                self._check_braces(rbraces, True, '}')
                b_num = (lb_num-1)>>1
                if b_num > 0:
                    nodes.append(Text('{' * b_num))
                mtext = self._replace_with_spaces(mtext)
                expr = '{{{}}}'.format(self._parse_node_str(mtext))
                nodes.append(Expression(expr, '{{{{{}}}}}'.format(mtext)))
                if b_num:
                    nodes.append(Text('}' * b_num))
            else:
                self._check_braces(lbraces, False, '{')
                self._check_braces(rbraces, False, '}')
                nodes.append(Text('{' * (lb_num>>1)))
                nodes.append(self._parse_node(mtext))
                nodes.append(Text('}' * (rb_num>>1)))

            if rtext:
                nodes.append(Text(rtext))

        return nodes

    def _is_dict_or_set_comp(self, text, _pattern=_PATTERN_COMP):
        # dict/set comprehensions
        if _pattern.match(text):
            try:
                self._ast_parse('{{{}}}'.format(text))
                print('yes', text)
            except SyntaxError:
                print('no', text)
                return False
            else:
                return True
        return False

    def _check_braces(self, braces, is_even, symbol):
        # '{{ {{ {{ {' style may exists.
        pieces = braces.split()

        for piece in pieces[:-1]:
            if len(piece)%2 != 0:
                raise SyntaxError(
                    'Single "{}" encountered in format string'.format(symbol))

        res = len(pieces[-1]) % 2
        if is_even and res != 0:
            raise SyntaxError(
                'Single "{}" encountered in format string'.format(symbol))
        if not is_even and res == 0:
            raise SyntaxError(
                'Single "{}" encountered in format string'.format(symbol))

    def _replace_with_spaces(self, text, _table=string.maketrans('\t\n\r\f\v', ' '*5)):
        return text.strip().translate(_table)

    def _parse_node(self, node_str):
        node_str = self._replace_with_spaces(node_str)
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
        splitd = node_str.rsplit(':', 1)
        if len(splitd) > 1:
            left, fmt_spec = splitd
            if not fmt_spec:
                raise SyntaxError('need format specifier after ":"')
            elif ')' in fmt_spec or '}' in fmt_spec or 'lambda' in left:
                left = node_str
        else:
            left = splitd[0]

        splitd = left.rsplit('!', 1)
        if len(splitd) > 1:
            expr, cvs_spec = splitd
            if cvs_spec not in _cvss:
                raise SyntaxError('optional conversions must be one of'
                                  ' {}'.format(_cvss))
        else:
            expr = splitd[0]

        return expr.strip()
