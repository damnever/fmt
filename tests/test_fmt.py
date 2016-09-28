# -*- coding: utf-8 -*-

import sys
from datetime import datetime
import fmt as  f


g_foo = 'global-foo'
g_bar = 'global-bar'


def func(x, y):
    return str(x) + str(y)


def get_namesapce(*_args):
    frame = sys._getframe(1)
    return frame.f_globals, frame.f_locals


def test_namespace():
    l_foo = 'local-foo'
    l_bar = 'local-bar'
    globals_, locals_ = get_namesapce()
    assert 'l_foo' in locals_
    assert 'l_bar' in locals_
    assert 'g_bar' in globals_
    assert 'g_bar' in globals_
    assert '@py_builtins' in globals_
    assert 'sys' in globals_
    assert 'func' in globals_


def test_closure_namespace():
    def outer(x):
        y = 'yy'
        def inner():
            z = 'zz'
            globals_, locals_ = get_namesapce(x, y)
            assert 'x' in locals_
            assert 'y' in locals_
            assert 'z' in locals_
            assert 'g_bar' in globals_
            assert 'g_bar' in globals_
            assert '@py_builtins' in globals_
            assert 'sys' in globals_
            assert 'func' in globals_
        return inner
    outer('xx')()


def test_fmt():
    l_foo = 'local-foo'
    l_bar = 'local-bar'
    ls_num = range(5)
    ls_ch = ['a', 'b', 'c', 'd', 'e']
    class Baz(object):
        def __str__(self):
            return 'BAZ'

    f.register('x', 13)
    f.register('y', 14)

    assert '' == f('')
    assert '{' == f('{{')
    assert '{ {}' == f('{{ {{}}')
    assert '}' == f('}}')
    assert '{} }' == f('{{}} }}')
    assert '{}' == f('{{}}')
    assert '{ }' == f('{{ }}')
    assert 'local-foo, local-bar' == f('{l_foo}, {l_bar}')
    for i in ls_num:
        assert str(i) == f('{ls_num[' + str(i) + ']}')
    for i, c in enumerate(ls_ch):
        assert "'{}'".format(c) == f('{ls_ch[' + str(i) + ']!r}')
    assert 'global-foo, global-bar' == f('{g_foo}, {g_bar}')
    assert '1314' == f('{func(x, y)}')

    def outer(arg):
        def inner():
            assert '{ outer-arg }' == f('{{ {arg} }}', arg)
        return inner
    outer('outer-arg')()

    assert '[0, 1, 2, 3, 4]' == f('{list(range(5))}')  # Py3 range return iterator
    assert '[0, 1, 2, 3, 4]' == f('{[i for i in ls_num]}')
    if sys.version_info[0] == 2:
        assert 'set([0, 1, 2, 3, 4])' == f('{{i for i in ls_num}}')
    else:
        assert '{0, 1, 2, 3, 4}' == f('{{i for i in ls_num}}')


    assert ("{0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e'}" ==
            f('{{k:v for k,v in zip(ls_num, ls_ch)}}'))
    assert '[1, 2, 3, 4, 5]' == f('{list(map(lambda x: x+1, ls_num))}')
    assert '3' == f('{1+2}')
    assert "'1314'" == f('{"13" + "14"!r}')
    assert "BAZ" == f('{Baz()!s}')
    assert '{}'.format(sys.argv) == f('{sys.argv}')
    assert ('int:23, hex:17, oct:0o27, bin:0b10111' ==
            f('int:{23:d}, hex:{23:x}, oct:{23:#o}, bin:{23:#b}'))
    assert '1,234,567,890' == f('{1234567890:,}')
    assert '1994-11-06' == f('{datetime(1994, 11, 6):%Y-%m-%d}')
