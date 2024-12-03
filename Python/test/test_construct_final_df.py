from .conftest import sample_data
import pandas as pd
from main import construct_final_df # Replace with the correct import


def test_construct_final_df_empty_dataframe():
    """Test when the input dataframe is empty."""
    empty_df = pd.DataFrame()
    result = construct_final_df(empty_df)
    pd.testing.assert_frame_equal(result, pd.DataFrame())


def test_construct_final_df_with_data(sample_data):
    """Test when the dataframe has data."""
    # Running the function with the sample data
    result = construct_final_df(sample_data)
    assert 'department_name' in result.columns
    assert 'aisle_name' in result.columns
    assert 'shelf_name' in result.columns
    assert 'attribute' in result.columns
    assert 'possible_values' in result.columns
    assert 'attribute_type' in result.columns
    assert 'review' in result.columns
    assert 'similar_attributes' in result.columns
    assert len(result) > 0
    assert result['department_name'].iloc[0] == 'Electronics'
    assert result['attribute_type'].iloc[0] == 'business'


def test_construct_final_df_with_business_and_technical_attributes(sample_data):
    """Test with both 'business' and 'technical' attribute types."""
    df = sample_data.copy()
    result = construct_final_df(df)
    assert (result['attribute_type'] == 'business').any()
    assert  (result['attribute_type'] == 'technical').any()


def test_construct_final_df_with_duplicates(sample_data):
    """Test removing duplicates in the final DataFrame."""
    df = sample_data.copy()
    df = pd.concat([df, df])

    result = construct_final_df(df)

    # Assert that the result has no duplicates
    assert result.duplicated().sum() == 0

