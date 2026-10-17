import pandas as pd
import pytest

from dataguard.ingestion import IngestionError, read_csv
from dataguard.profiling import column_profile, iqr_mask, profile


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"   ",
        b"a,b\n",
        b"a,a\n1,2",
        b",b\n1,2",
        b"a,b\n1,2,3",
        b"a,b\n1",
        b'a,b\n"unclosed,2',
        b"a\n\x00",
    ],
)
def test_reject_empty_malformed_or_ambiguous_csv(content):
    with pytest.raises(IngestionError):
        read_csv(content)


def test_identifier_encoding_and_missing_values_preserved():
    content = "CustomerID;Description;amount\n00123;café;3\n00456;NA;\n".encode("cp1252")
    with pytest.raises(IngestionError, match="decode"):
        read_csv(content, delimiter=";")
    loaded = read_csv(content, delimiter=";", encoding="cp1252")
    assert loaded.frame.CustomerID.tolist() == ["00123", "00456"]
    assert loaded.frame.Description.tolist() == ["café", "NA"]
    assert pd.isna(loaded.frame.amount.iloc[1])
    assert loaded.encoding == "cp1252"


def test_quoted_embedded_newline_and_bom():
    data = read_csv('\ufeffname,value\n"first\nsecond",2\n'.encode())
    assert data.frame.iloc[0, 0] == "first\nsecond"
    assert len(data.frame) == 1


def test_measurement_acid_is_numeric_while_identifiers_stay_text():
    frame = read_csv(b"citric_acid,CustomerID,record_id\n0.4,00123,0005\n").frame
    assert pd.api.types.is_numeric_dtype(frame.citric_acid)
    assert frame.CustomerID.iloc[0] == "00123" and frame.record_id.iloc[0] == "0005"


@pytest.mark.parametrize(
    "kwargs", [{"max_rows": 1}, {"max_bytes": 3}, {"encoding": "utf-16"}, {"delimiter": "xx"}]
)
def test_ingestion_limits(kwargs):
    with pytest.raises(IngestionError):
        read_csv(b"a,b\n1,2\n3,4", **kwargs)


def test_profile_expected_denominators_and_immutability():
    frame = pd.DataFrame({"a": [1, 1, None], "b": ["x", "x", "z"]})
    before = frame.copy(deep=True)
    summary = profile(frame)
    table = column_profile(frame).set_index("column")
    assert summary["duplicate_rows"] == 1
    assert summary["missing_cells"] == 1
    assert table.loc["a", "missing_pct"] == pytest.approx(100 / 3)
    assert table.loc["a", "unique_count"] == 1
    pd.testing.assert_frame_equal(frame, before)


def test_empty_profile_and_iqr_edge_cases():
    assert profile(pd.DataFrame({"x": []}))["rows"] == 0
    assert column_profile(pd.DataFrame()).empty
    assert not iqr_mask(pd.Series([None, None])).any()
    assert not iqr_mask(pd.Series([2, 2, 2, 2, 100])).any()
    assert iqr_mask(pd.Series([0, 1, 2, 3, 4, 100])).iloc[-1]
