# -*- coding: utf-8 -*-

import pytest
from fmt.fmt import Text, Constant, Expression


def test_flyweight():
    assert id(Text('foo', 'bar')) == id(Text('foo', 'bar'))
    assert id(Constant('foo', 'bar')) == id(Constant('foo', 'bar'))
    assert id(Expression('foo', 'bar')) == id(Expression('foo', 'bar'))

    assert id(Text('foo', 'bar')) != id(Text('bar', 'foo'))
    assert id(Constant('foo', 'bar')) != id(Constant('bar', 'foo'))
    assert id(Expression('foo', 'bar')) != id(Expression('bar', 'foo'))

    assert id(Text('foo', 'bar')) != id(Constant('foo', 'bar'))
    assert id(Text('foo', 'bar')) != id(Expression('foo', 'bar'))
    assert id(Constant('foo', 'bar')) != id(Expression('foo', 'bar'))


def test_Text():
    text = 'I am a good man, /(ㄒoㄒ)/~~'
    assert text == Text(text).generate(None)
    texts = ['yes', 'or', 'no']
    assert ''.join(texts) == Text(*texts).generate(None)


def test_Constant():
    name = 'foo'
    fmt = '{foo}'
    ns = {name: 'bar'}
    const = Constant(name, fmt)

    assert fmt.format(**ns) == const.generate(ns)
    with pytest.raises(NameError):
        const.generate({})


def test_Expression():
    def func(dd):
        return str(dd) + '++'
    ns = {'dd': '--', 'func': func}
    expr = 'func(dd)'
    fmt = '{func(dd) }'
    expression = Expression(expr, fmt)

    assert '{}'.format(func(ns['dd'])) == expression.generate(ns)
    with pytest.raises(NameError):
        expression.generate({})
