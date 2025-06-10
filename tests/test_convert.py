import os
import sys
from types import ModuleType

# Provide a minimal stub for ``pandas`` so ``convert`` can be imported even if
# the real library is not installed in the test environment.
sys.modules.setdefault('pandas', ModuleType('pandas'))

# Ensure repository root is on the path so ``convert`` can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from convert import convert_defect_type


class DummyDataFrame:
    """Minimal structure mimicking ``pandas.DataFrame`` for tests."""

    def __init__(self, defect_types):
        self._rows = [{'DefectType': dt} for dt in defect_types]

    def iterrows(self):
        for idx, row in enumerate(self._rows):
            yield idx, row


def test_convert_defect_type():
    df = DummyDataFrame(['good1', 'bad1', 'good2'])
    good_defects = ['good1', 'good2']
    result = convert_defect_type(df, good_defects)
    assert result == [1, 0, 1]


