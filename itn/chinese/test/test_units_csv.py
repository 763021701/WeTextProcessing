# Copyright (c) 2026
# Batch ITN checks against corpus derived from raw/all_units_with_pronunciation.csv.
# Default: skipped so CI is not flooded by expected mismatches.
# Run: ITN_TEST_CSV_UNITS=1 python -m pytest itn/chinese/test/test_units_csv.py -q

import os

import pytest

from itn.chinese.inverse_normalizer import InverseNormalizer
from itn.chinese.test.utils import parse_test_case

_csv_cases = list(parse_test_case("data/units_pronunciation_from_csv.txt"))

if os.environ.get("ITN_TEST_CSV_UNITS") != "1":
    pytestmark = pytest.mark.skip(
        reason="Set ITN_TEST_CSV_UNITS=1 to run ~470 CSV-derived unit ITN cases",
    )


class TestUnitsFromCsvCorpus:
    normalizer = InverseNormalizer(
        overwrite_cache=False,
        enable_standalone_number=True,
        enable_0_to_9=True,
        enable_million=False,
    )

    @pytest.mark.parametrize("spoken, written", _csv_cases)
    def test_csv_pronunciation_to_unit(self, spoken, written):
        assert self.normalizer.normalize(spoken) == written
