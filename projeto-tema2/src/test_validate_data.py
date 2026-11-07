import pandas as pd
import pytest
from src.validate_data import (
    check_missing_and_duplicates,
    check_negative_values,
    check_constant_columns
)

def test_constant_columns_detecta_coluna_constante():
    df = pd.DataFrame({"a": [1, 1, 1], "b": [1, 2, 3]})
    assert check_constant_columns(df) == ["a"]


def test_constant_columns_sem_constantes():
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    assert check_constant_columns(df) == []


def test_negative_values_conta_negativos():
    df = pd.DataFrame({"x": [-1, 2, 3, -4]})
    result = check_negative_values(df)
    assert result.loc["x", "negatives"] == 2


def test_missing_and_duplicates_conta_nulos():
    df = pd.DataFrame({"x": [1, None, 3, 3]})
    result = check_missing_and_duplicates(df)
    assert result.loc["x", "nulls"] == 1
    assert result.loc["x", "duplicated_values"] == 1