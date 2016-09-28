# -*- coding: utf-8 -*-

import pytest
from fmt.fmt import Parser, Text, Constant, Expression


def test_parse_node_str():
    parser = Parser('')

    assert 'name' == parser._parse_node_str('name ')
    assert 'name' == parser._parse_node_str('name!r')
    assert 'name' == parser._parse_node_str('name!s')
    assert 'name' == parser._parse_node_str('name!a')
    assert 'name' == parser._parse_node_str('name:fmt')
    assert 'name' == parser._parse_node_str('name!r:fmt')
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


def test_is_dict_or_set_comp():
    parser = Parser('')
    assert parser._is_dict_or_set_comp('i for i in range(10)')
    assert parser._is_dict_or_set_comp('k:v for k,v in d.items()')
    assert parser._is_dict_or_set_comp('k:v for k,v in zip(ls1, ls2)')
    assert not parser._is_dict_or_set_comp('for')
    assert not parser._is_dict_or_set_comp('for_in')


def test_replace_with_spaces():
    parser = Parser('')
    assert ('a b c d e f  g' ==
            parser._replace_with_spaces(' a b\nc\rd\fe\vf\n\ng '))


def test_check_braces():
    parser = Parser('')

    assert '' == parser._check_braces('{', False, '{')
    assert '{' == parser._check_braces('{{{', False, '{')
    assert '{ ' == parser._check_braces('{{ {', False, '{')
    assert '{ { ' == parser._check_braces('{{ {{ {', False, '{')
    assert '' == parser._check_braces('{{', True, '{')
    assert ' }' == parser._check_braces('} }}', False, '}')
    assert '{ ' == parser._check_braces('{{ {{', True, '{')
    assert '{ {' == parser._check_braces('{{ {{', True, '{', True)
    assert '{{' == parser._check_braces('{{{{', True, '{', True)

    with pytest.raises(SyntaxError):
        parser._check_braces('{{{', True, '{')
    with pytest.raises(SyntaxError):
        parser._check_braces('{', True, '{')
    with pytest.raises(SyntaxError):
        parser._check_braces('{{ {', True, '{')
    with pytest.raises(SyntaxError):
        parser._check_braces('{ { { {', True, '{', True)
    with pytest.raises(SyntaxError):
        parser._check_braces('{{', False, '{')
    with pytest.raises(SyntaxError):
        parser._check_braces('{{ {{', False, '{')


def test_parse_with_only_text():
    nodes = Parser('').parse()
    assert 1 == len(nodes)
    assert isinstance(nodes[0], Text)
    assert '' == nodes[0]._content

    nodes = Parser('  ').parse()
    assert 1 == len(nodes)
    assert isinstance(nodes[0], Text)
    assert '  ' == nodes[0]._content

    nodes = Parser('name').parse()
    assert 1 == len(nodes)
    assert isinstance(nodes[0], Text)
    assert 'name' == nodes[0]._content

    nodes = Parser('{{}}').parse()
    assert 1 == len(nodes)
    assert isinstance(nodes[0], Text)
    assert '{}' == nodes[0]._content

    nodes = Parser('{{name}}').parse()
    assert 1 == len(nodes)
    assert isinstance(nodes[0], Text)
    assert '{name}' == nodes[0]._content

    nodes = Parser('text{{name}}').parse()
    assert 2 == len(nodes)
    assert isinstance(nodes[0], Text)
    assert 'text' == nodes[0]._content
    assert isinstance(nodes[1], Text)
    assert '{name}' == nodes[1]._content

    nodes = Parser('{{name}}text').parse()
    assert 2 == len(nodes)
    assert isinstance(nodes[0], Text)
    assert '{name}' == nodes[0]._content
    assert isinstance(nodes[1], Text)
    assert 'text' == nodes[1]._content

    nodes = Parser('{{ name }} ').parse()
    assert 2 == len(nodes)
    assert isinstance(nodes[0], Text)
    assert '{ name }' == nodes[0]._content
    assert isinstance(nodes[1], Text)
    assert ' ' == nodes[1]._content


def test_parse_constant():
    nodes = Parser('{name}').parse()
    assert 1 == len(nodes)
    assert isinstance(nodes[0], Constant)
    assert 'name' == nodes[0]._name
    assert '{name}' == nodes[0]._fmt

    nodes = Parser('{ name }').parse()
    assert 1 == len(nodes)
    assert isinstance(nodes[0], Constant)
    assert 'name' == nodes[0]._name
    assert '{name}' == nodes[0]._fmt

    nodes = Parser('text {{{name} text').parse()
    assert 4 == len(nodes)
    assert isinstance(nodes[0], Text)
    assert 'text ' == nodes[0]._content
    assert isinstance(nodes[1], Text)
    assert '{' == nodes[1]._content
    assert isinstance(nodes[2], Constant)
    assert 'name' == nodes[2]._name
    assert '{name}' == nodes[2]._fmt
    assert isinstance(nodes[3], Text)
    assert ' text' == nodes[3]._content

    nodes = Parser('text {{ {name} text').parse()
    assert 4 == len(nodes)
    assert isinstance(nodes[0], Text)
    assert 'text ' == nodes[0]._content
    assert isinstance(nodes[1], Text)
    assert '{ ' == nodes[1]._content
    assert isinstance(nodes[2], Constant)
    assert 'name' == nodes[2]._name
    assert '{name}' == nodes[2]._fmt
    assert isinstance(nodes[3], Text)
    assert ' text' == nodes[3]._content

    nodes = Parser('text {name}}} text').parse()
    assert 4 == len(nodes)
    assert isinstance(nodes[0], Text)
    assert 'text ' == nodes[0]._content
    assert isinstance(nodes[1], Constant)
    assert 'name' == nodes[1]._name
    assert '{name}' == nodes[1]._fmt
    assert isinstance(nodes[2], Text)
    assert '}' == nodes[2]._content
    assert isinstance(nodes[3], Text)
    assert ' text' == nodes[3]._content

    nodes = Parser('text {name} }} text').parse()
    assert 4 == len(nodes)
    assert isinstance(nodes[0], Text)
    assert 'text ' == nodes[0]._content
    assert isinstance(nodes[1], Constant)
    assert 'name' == nodes[1]._name
    assert '{name}' == nodes[1]._fmt
    assert isinstance(nodes[2], Text)
    assert ' }' == nodes[2]._content
    assert isinstance(nodes[3], Text)
    assert ' text' == nodes[3]._content

    nodes = Parser('text {name} text').parse()
    assert 3 == len(nodes)
    assert isinstance(nodes[0], Text)
    assert 'text ' == nodes[0]._content
    assert isinstance(nodes[1], Constant)
    assert 'name' == nodes[1]._name
    assert '{name}' == nodes[1]._fmt
    assert isinstance(nodes[2], Text)
    assert ' text' == nodes[2]._content

    nodes = Parser('text {name}done').parse()
    assert 3 == len(nodes)
    assert isinstance(nodes[0], Text)
    assert 'text ' == nodes[0]._content
    assert isinstance(nodes[1], Constant)
    assert 'name' == nodes[1]._name
    assert '{name}' == nodes[1]._fmt
    assert isinstance(nodes[2], Text)
    assert 'done' == nodes[2]._content

    nodes = Parser('text {{{name}}}').parse()
    assert 4 == len(nodes)
    assert isinstance(nodes[0], Text)
    assert 'text ' == nodes[0]._content
    assert isinstance(nodes[1], Text)
    assert '{' == nodes[1]._content
    assert isinstance(nodes[2], Constant)
    assert 'name' == nodes[2]._name
    assert '{name}' == nodes[2]._fmt
    assert isinstance(nodes[3], Text)
    assert '}' == nodes[3]._content


def test_parse_expression():
    nodes = Parser('text {{v for v in range(10)}}').parse()
    assert 2 == len(nodes)
    assert isinstance(nodes[0], Text)
    assert 'text ' == nodes[0]._content
    assert isinstance(nodes[1], Expression)
    assert 'name' == nodes[1]._name
    assert '{name}' == nodes[1]._fmt
    assert '{v for v in range(10)}' == nodes[1]._expr

    nodes = Parser('text {{k:v for k,v in zip(ls1, ls2)}}').parse()
    assert 2 == len(nodes)
    assert isinstance(nodes[0], Text)
    assert 'text ' == nodes[0]._content
    assert isinstance(nodes[1], Expression)
    assert 'name' == nodes[1]._name
    assert '{k:v for k,v in zip(ls1, ls2)}' == nodes[1]._expr
    assert '{name}' == nodes[1]._fmt

    nodes = Parser('text {map(lambda x: x, ls)}').parse()
    assert 2 == len(nodes)
    assert isinstance(nodes[0], Text)
    assert 'text ' == nodes[0]._content
    assert isinstance(nodes[1], Expression)
    assert 'name' == nodes[1]._name
    assert '{name}' == nodes[1]._fmt
    assert 'map(lambda x: x, ls)' == nodes[1]._expr

    nodes = Parser('text {func()}').parse()
    assert 2 == len(nodes)
    assert isinstance(nodes[0], Text)
    assert 'text ' == nodes[0]._content
    assert isinstance(nodes[1], Expression)
    assert 'name' == nodes[1]._name
    assert '{name}' == nodes[1]._fmt
    assert 'func()' == nodes[1]._expr


def test_parser_with_error():
    with pytest.raises(SyntaxError):
        Parser('{').parse()
    with pytest.raises(SyntaxError):
        Parser('}').parse()
    with pytest.raises(SyntaxError):
        Parser('{}').parse()
    with pytest.raises(SyntaxError):
        Parser('text {name').parse()
    with pytest.raises(SyntaxError):
        Parser('text {{name}').parse()
    with pytest.raises(SyntaxError):
        Parser('text { {name').parse()
    with pytest.raises(SyntaxError):
        Parser('text {{ { {name').parse()
    with pytest.raises(SyntaxError):
        Parser('text {name}}').parse()
    with pytest.raises(SyntaxError):
        Parser('text {name} }').parse()
    with pytest.raises(SyntaxError):
        Parser('text {name} }} }').parse()
