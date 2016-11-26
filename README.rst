f-strings(Python 3.6) style literal string interpolation.
==========================================================

.. image:: https://img.shields.io/travis/damnever/fmt.svg?style=flat-square
    :target: https://travis-ci.org/damnever/fmt

.. image:: https://img.shields.io/pypi/v/fmt.svg?style=flat-square
    :target: https://pypi.python.org/pypi/fmt


Using `f-strings(PEP 498) <https://www.python.org/dev/peps/pep-0498/>`_ style literal string interpolation without Python 3.6.


Usages
------

- Accessing the globals and locals.

    .. code:: python

        import os
        import fmt as f

        g_foo = 'global-foo'
        g_bar = 'global-bar'
        g_num = 23
        g_ls = [1, 2, 3]

        def scope():
            l_foo = 'local-foo'
            l_bar = 'local-bar'
            print( f('{l_foo}, {l_bar}') )    # 'local-foo, local-bar'
            print( f('{g_foo}, {g_bar!r}') )  # "global-foo, 'global-bar'"

        scope()
        print( f('{{ }}') )                   # '{ }'
        print( f('hex: {g_num:#x}') )         # '0x17'
        print( f('{os.EX_OK}') )              # '0'
        print( f('{g_ls[0]}, {g_ls[1]}, {g_ls[2]}') )  # '1, 2, 3'


- **NOTE**: **Closure** will be a little tricky, must pass the outside scope variables as arguments to f,
  which added a reference to inside the closure in order this can work.

    .. code:: python

        import fmt as f

        def outer(x='xx'):
            y = 'yy'
            def inner():
                print( f('{x}, {y}', x, y) )  # "xx, yy"
            return inner

        outer()()


- Expression evaluation.

    .. code:: python

        from datetime import datetime
        import fmt as f

        class S(object):
            def __str__(self):
                return 'hello'
            def __repr__(self):
                return 'hi'
            def __format__(self, fmt):
                return 'abcdefg'[int(fmt)]

        print( f('{1234567890:,}') )             # '1,234,567,890'
        print( f('{1 + 2}') )                    # '3'
        print( f('{str(1 + 2)!r}') )             # "'3'"
        print( f('{[i for i in range(5)]}') )    # '[0, 1, 2, 3, 4]'
        ls = range(5)
        print( f('{{i for i in ls}}') )          # 'set([0, 1, 2, 3, 4])' or '{0, 1, 2, 3, 4}'
        print( f('{{k:v for k,v in zip(range(3), range(3, 6))}}') )  # '{0: 3, 1: 4, 2: 5}'
        print( f('{datetime(1994, 11, 6):%Y-%m-%d}') )               # '1994-11-06'
        print( f('{list(map(lambda x: x+1, range(3)))}') )           # '[1, 2, 3]'
        print( f('{S()!s}, {S()!r}, {S():1}') )                      # 'hello, hi, b'


- Also, you can register some namespaces for convenience.

    .. code:: python

        import fmt as f

        f.mregister({'x': 1, 'y': 2})  # register multiple
        f.register('z', 3)             # register only one

        def func(x, y):
            return x + y

        print( f('{func(x, y)}') )  # '3'
        print( f('{func(x, z)}') )  # '4'
        print( f('{func(y, z)}') )  # '5'


- **NOTE**: ``locals()`` maybe cover the ``globals()``, ``globals()`` maybe cover the namespaces that you registered.


Installation
------------

Install by pip: ::

    [sudo] pip install fmt -U


LICENSE
-------

`The BSD 3-Clause License <https://github.com/damnever/fmt/blob/master/LICENSE>`_
