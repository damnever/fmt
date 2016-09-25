f-strings(Python 3.6) style literal string interpolation.
==========================================================

Ref: https://www.python.org/dev/peps/pep-0498/

Currently I got stuck in some corner cases, need to find a better way, define a micro-language?..

Example
-------

.. code:: python

    import fmt as f

    a = 0
    b = 'bb'

    def dd():
        return 'dd'

    def func():
        c = 'c@'
        print(f("a = {a}, b = {b!r}, c = {c}, dd() = {{{ dd() }}}, set == {{{{k for k in range(5)}}}}"))

    # A little ticky...
    def outer(foo):
        bar = 'bar'
        def inner():
            print(f("a = {a}, b = {b}, foo = {foo}, bar = {bar}", foo, bar))
        return inner

    func()  # a = 0, b = 'bb', c = c@, dd() = {dd}, set == {set([0, 1, 2, 3, 4])}
    outer('foo')()  # a = 0, b = bb, foo = foo, bar = bar
