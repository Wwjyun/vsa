import os
import sys

# Ensure repository root is on the path so ``search`` can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import search


def test_perform_search_path():
    result = search.perform_search('opt', '123', 'CODE', 'btn')
    assert result == 'D:/Database-PC/opt/map/123/btn/CODE'

