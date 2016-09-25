# -*- coding: utf-8 -*-

import pytest
from fmt.fmt import Parser, Text, Constant, Expression, Reader


def test_parse_node_str():
    parser = Parser('')

    assert 'name' == parser._parse_node_str('name ')
    assert 'name' == parser._parse_node_str('name!r')
    assert 'name' == parser._parse_node_str('name!s')
    assert 'name' == parser._parse_node_str('name!a')
    assert 'name' == parser._parse_node_str('name:fmt')
    assert 'name' == parser._parse_node_str('name!r:fmt')
    assert ('{k:v for kv in d.items()}' ==
            parser._parse_node_str('{k:v for kv in d.items()}'))
    assert ('{i for i in range(5)}' ==
            parser._parse_node_str('{i for i in range(5)}'))
    assert ('map(lambda x: x, ls)' ==
            parser._parse_node_str('map(lambda x: x, ls)'))


    with pytest.raises(SyntaxError):
        parser._parse_node_str('name!n')
    with pytest.raises(SyntaxError):
        parser._parse_node_str('name:')


def test_parse_node():
    parser = Parser('')

    node_str = 'name!r:fmt'
    node = parser._parse_node(node_str)
    assert isinstance(node, Constant)
    assert node._fmt == '{' + node_str + '}'

    node_strs = ['[i for i in ls]', 'func()', 'map(lambda x: x, ls)']
    for node_str in node_strs:
        node = parser._parse_node(node_str)
        assert isinstance(node, Expression)
        assert node._fmt == '{name}'

    with pytest.raises(SyntaxError):
        parser._parse_node('a = b')


def test_parse_escape():
    # Note: assume there is one '{' has been readed
    assert (2, False, True) == Parser('{ {')._parse_escape()
    assert (3, False, False) == Parser('{{ ')._parse_escape()
    assert (3, False, False) == Parser('{{ {')._parse_escape()
    assert (4, False, True) == Parser('{{{ {')._parse_escape()
    assert (4, False, True) == Parser('{{{ ')._parse_escape()

    with pytest.raises(Reader.EOF):
        Parser('{{{')._parse_escape()


def test_parse():
    nodes = Parser('{name}').parse()
    assert isinstance(nodes[0], Text)
    assert '' == nodes[0]._content
    assert isinstance(nodes[1], Constant)
    assert 'name' == nodes[1]._name
    assert '{name}' == nodes[1]._fmt

    nodes = Parser('text {name} text').parse()
    assert isinstance(nodes[0], Text)
    assert 'text ' == nodes[0]._content
    assert isinstance(nodes[1], Constant)
    assert 'name' == nodes[1]._name
    assert '{name}' == nodes[1]._fmt
    assert isinstance(nodes[2], Text)
    assert ' text' == nodes[2]._content

    nodes = Parser('text {name}done').parse()
    assert isinstance(nodes[0], Text)
    assert 'text ' == nodes[0]._content
    assert isinstance(nodes[1], Constant)
    assert 'name' == nodes[1]._name
    assert '{name}' == nodes[1]._fmt
    assert isinstance(nodes[2], Text)
    assert 'done' == nodes[2]._content

    nodes = Parser('text {{name}}').parse()
    assert isinstance(nodes[0], Text)
    assert 'text ' == nodes[0]._content
    assert isinstance(nodes[1], Text)
    assert '{' == nodes[1]._content
    assert isinstance(nodes[2], Text)
    assert 'name}}' == nodes[2]._content

    nodes = Parser('text {{{name}}}').parse()
    assert isinstance(nodes[0], Text)
    assert 'text ' == nodes[0]._content
    assert isinstance(nodes[1], Text)
    assert '{' == nodes[1]._content
    assert isinstance(nodes[2], Constant)
    assert 'name' == nodes[2]._name
    assert '{name}' == nodes[2]._fmt
    assert isinstance(nodes[3], Text)
    assert '}' == nodes[3]._content

    nodes = Parser('text {{k:v for k,v in zip(ls1, ls2)}}').parse()
    assert isinstance(nodes[0], Text)
    assert 'text ' == nodes[0]._content
    assert isinstance(nodes[1], Expression)
    assert 'name' == nodes[1]._name
    assert '{k:v for k,v in zip(ls1, ls2)}' == nodes[1]._expr
    assert '{name}' == nodes[1]._fmt

    nodes = Parser('text {map(lambda x: x, ls)}').parse()
    assert isinstance(nodes[0], Text)
    assert 'text ' == nodes[0]._content
    assert isinstance(nodes[1], Expression)
    assert 'name' == nodes[1]._name
    assert 'map(lambda x: x, ls)' == nodes[1]._expr
    assert '{name}' == nodes[1]._fmt

    with pytest.raises(SyntaxError):
        Parser('text {name').parse()
    with pytest.raises(SyntaxError):
        Parser('text {{name}').parse()
    with pytest.raises(SyntaxError):
        Parser('text {{{name}').parse()
    with pytest.raises(SyntaxError):
        Parser('text {name}}').parse()
    with pytest.raises(SyntaxError):
        Parser('text {{name}}}').parse()
