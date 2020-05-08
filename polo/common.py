"""
common.py
============
This file contains methods used by multiple other files.
"""

import itertools
from flask import session, redirect
from polo import app


def authenticate(f):
    def wrapper():
        if app.config['BYPASS_AUTH']:
            session['username'] = "development"
        elif 'username' not in session or not session['username']:
            return redirect('/auth')
        return f()

    return wrapper


def get_result(resultproxy):
    """
    :param resultproxy:
    :return: list of key/value pairs from a database query result
    """
    return [{column: value for column, value in rowproxy.items()} for rowproxy in resultproxy]


def merge_dicts(dict1, dict2, key):
    """
    Merge two dictionaries based on a single key.
    Inspired from https://stackoverflow.com/questions/13975021/merge-join-lists-of-dictionaries-based-on-a-common-value-in-python
    :param dict1:
    :param dict2:
    :param key:
    :return: list of merged data
    """
    lst = sorted(itertools.chain(dict1, dict2), key=lambda x: x[key])
    list_c = []
    for k, v in itertools.groupby(lst, key=lambda x: x[key]):
        d = {}
        for dct in v:
            d.update(dct)
        list_c.append(d)
    return list_c
