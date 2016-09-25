# -*- coding: utf-8 -*-

import pytest
from fmt.fmt import Reader


@pytest.fixture(scope='module')
def f_str():
    return 'a = {a}, b = {b!r}, c = {{{c()}}}'


@pytest.fixture(scope='funciton')
def reader(f_str):
    return Reader(f_str)


def test_read_util(f_str, reader):
    assert f_str[:f_str.find('{')] == reader.read_util('{')
    assert reader.pos == 4
    pos = f_str.find('}', 4)
    assert f_str[4: pos] == reader.read_util('{')
    assert reader.pos == pos
    assert reader.read_util('8') is None
    reader._next_pos = len(f_str)
    with pytest.raises(Reader.EOF):
        reader.read_util('{')


def test_read(f_str, reader):
    assert f_str[0] == reader.read()
    assert reader.pos == 1
    assert f_str[1: 5] == reader.read(4)
    assert reader.pos == 5
    assert f_str[5: len(f_str)] == reader.read(len(f_str)-5)
    with pytest.raises(Reader.EOF):
        reader.read()


def test_peek(f_str, reader):
    for i, ch in enumerate(f_str):
        assert reader.peek(i) == ch


def test_is_eof(f_str, reader):
    reader.read(len(f_str))
    assert reader.is_eof()
