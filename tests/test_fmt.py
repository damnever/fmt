# -*- coding: utf-8 -*-

import sys


g_foo = 'global-foo'
g_bar = 'global-bar'


def func(x, y):
    return str(x + y)


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

