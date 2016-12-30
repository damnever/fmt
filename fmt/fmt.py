# -*- coding: utf-8 -*-

from __future__ import absolute_import

import re
import ast
import sys
from copy import deepcopy
from functools import partial


PY3 = sys.version_info[0] == 3
if PY3:
    fmt_types = str, bytes
else:
    fmt_types = basestring, unicode  # noqa: F821


class Fmt(object):

    def __init__(self):
        self._g_ns = {}
        self._nodes_cache = {}

    def register(self, name, value, update=False):
        if not update and name in self._g_ns:
            raise ValueError('namespace "{}" already registered'.format(name))
        self._g_ns[name] = value

    def mregister(self, ns, update=False):
        for k, v in ns.items():
            self.register(k, v, update)

    def __call__(self, f_str, *_args):
        if not isinstance(f_str, fmt_types):
            raise ValueError('Unsupported type as format '
                             'string: {}({})'.format(type(f_str), f_str))
        frame = sys._getframe(1)
        # locals will cover globals
        ns = deepcopy(self._g_ns)
        ns.update(frame.f_globals)
        ns.update(frame.f_locals)

        # cache nodes, if already parsed
        nodes = self._nodes_cache.get(f_str, None)
        if nodes is None:
            nodes = Parser(f_str).parse()
            self._nodes_cache[f_str] = nodes

        try:
            return generate(nodes, ns)
        finally:
            del frame  # avoid reference cycle


def generate(nodes, namespace):
    contents = []
    for node in nodes:
        contents.append(node.generate(namespace))
    return ''.join(contents)


class Node(object):
    # flyweight pattern: cache instances
    _instances = {}

    def __new__(cls, *args, **kwargs):
        key = (cls, args, tuple(kwargs.items()))
        instance = cls._instances.get(key, None)
        if instance is None:
            instance = super(Node, cls).__new__(cls)
            instance.__init__(*args, **kwargs)
            cls._instances[key] = instance
        return instance

    def generate(self, ns):
        raise NotImplementedError()


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
        try:
            value = namespace[name]
        except KeyError:
            raise NameError(
                '"{}" cannot be found in any namespaces.'.format(name))
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
                '"{}" cannot be found in any namespaces.'.format(name))
        return self._fmt.format(**ns)


class Parser(object):
    _PATTERN_SPEC = re.compile(
        r"""
        (?P<ltext>[^\{\}]*)
        (?P<lbrace>\{)?
            (?P<lbraces>(?(lbrace)[\s\{]*))
        (?P<mtext>[^\{\}]*)
        (?P<rbrace>\})?
            (?P<rbraces>(?(rbrace)[\s\}]*))
        (?P<rtext>[^\{\}]*)
        """, re.S | re.X | re.M
    )
    _PATTERN_COMP = re.compile(
        r'[a-zA-Z0-9_:]+\s+for\s+[a-zA-Z0-9_,]+\s+in\s+.+',
        re.S | re.X | re.M)
    _ast_parse = partial(ast.parse, filename='<f-strings>', mode='eval')

    def __init__(self, f_str):
        self._f_str = f_str

    def parse(self, _pattern=_PATTERN_SPEC):
        f_str = self._f_str
        if not f_str or f_str.isspace():
            return [Text(f_str)]

        nodes = []

        for match_obj in _pattern.finditer(f_str):
            groups = match_obj.groupdict()
            ltext = groups['ltext'] or ''
            lbraces = (groups['lbrace'] or '') + (groups['lbraces'] or '')
            mtext = (groups['mtext'] or '')
            rbraces = (groups['rbrace'] or '') + (groups['rbraces'] or '')
            rtext = groups['rtext'] or ''
            if lbraces:
                raw, lbraces = lbraces, lbraces.rstrip()
                mtext = raw[len(lbraces):] + mtext
            if rbraces:
                raw, rbraces = rbraces, rbraces.rstrip()
                rtext = raw[len(rbraces):] + rtext

            if all(s == '' for s in (ltext, lbraces, mtext, rbraces, rtext)):
                continue

            if not lbraces and not rbraces:
                nodes.append(Text(ltext, mtext, rtext))
                continue

            if ltext:
                nodes.append(Text(ltext))

            if not mtext or mtext.isspace() or not (lbraces and rbraces):
                texts = []
                if lbraces:
                    texts.append(self._check_braces(lbraces, True, '{', True))
                texts.append(mtext)
                if rbraces:
                    texts.append(self._check_braces(rbraces, True, '}', True))
                nodes.append(Text(*texts))
            else:
                is_comp = self._is_dict_or_set_comp(mtext)
                if is_comp:
                    lbtext = self._check_braces(lbraces, True, '{')
                    rbtext = self._check_braces(rbraces, True, '}')
                    if lbtext:
                        nodes.append(Text(lbtext))
                    expr = '{{{}}}'.format(self._replace_with_spaces(mtext))
                    nodes.append(Expression(expr, '{{{}}}'.format(expr)))
                    if rbtext:
                        nodes.append(Text(rbtext))
                else:
                    lb_num, rb_num = lbraces.count('{'), rbraces.count('}')
                    if lb_num == rb_num and lb_num > 0 and lb_num % 2 == 0:
                        texts = []
                        if lbraces:
                            texts.append(
                                self._check_braces(lbraces, True, '{', True))
                        texts.append(mtext)
                        if rbraces:
                            texts.append(
                                self._check_braces(rbraces, True, '}', True))
                        nodes.append(Text(*texts))
                    else:
                        lbtext = self._check_braces(lbraces, False, '{')
                        rbtext = self._check_braces(rbraces, False, '}')
                        lb_num = lb_num >> 1
                        if lbtext:
                            nodes.append(Text(lbtext))
                        nodes.append(self._parse_node(mtext))
                        rb_num = rb_num >> 1
                        if rbtext:
                            nodes.append(Text(rbtext))

            if rtext:
                nodes.append(Text(rtext))

        return nodes

    def _is_dict_or_set_comp(self, text, _pattern=_PATTERN_COMP):
        # dict/set comprehensions
        if _pattern.match(text):
            try:
                self._ast_parse('{{{}}}'.format(text))
            except SyntaxError:
                return False
            else:
                return True
        return False

    def _check_braces(self, braces, is_even, symbol, strict_even=False):
        # .........
        btexts = []
        pieces = braces.split()
        if symbol == '}':
            pieces = pieces[::-1]
            braces = braces[::-1]

        if len(pieces) == 1:
            nbraces = len(braces)
            mod = nbraces % 2
            if is_even:
                if mod != 0:
                    raise SyntaxError(
                        'Single "{}" encountered in format string'.format(
                            symbol))
            elif mod != 1:
                raise SyntaxError(
                    'Single "{}" encountered in format string'.format(symbol))
            if not strict_even:
                nbraces -= 1
            return symbol * (nbraces >> 1)

        pos, has_rest = 0, False
        for idx, piece in enumerate(pieces):
            div, mod = divmod(len(piece), 2)
            if mod != 0:
                if is_even and strict_even:
                    raise SyntaxError(
                        'Single "{}" encountered in format string'.format(
                            symbol)
                    )
                else:
                    has_rest = True
                    break

            if idx == 0:
                pos += len(piece)
            else:
                end = braces.find(piece, pos)
                btexts.append(braces[pos: end])
                pos = end + len(piece)
            btexts.append(symbol * div)

        if has_rest:
            end = braces.find(piece, pos)
            btexts.append(braces[pos: end])
        else:
            if not strict_even:
                btexts.pop()

        rest = len(''.join(pieces[idx:]))
        if is_even:
            if rest != 2:
                raise SyntaxError(
                    'Single "{}" encountered in format string'.format(symbol))
        elif rest != 1:
            raise SyntaxError(
                'Single "{}" encountered in format string'.format(symbol))

        if symbol == '}':
            btexts = btexts[::-1]
        return ''.join(btexts)

    def _replace_with_spaces(self, text, _repl='\t\n\r\f\v'):
        text = text.strip()
        for r in _repl:
            text = text.replace(r, ' ')
        return text

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
            elif 'lambda' in left:
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
