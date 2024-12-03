from .conftest import app, sample_data, mock_bigquery_client_success, mock_credentials
import flask
from flask import Flask, jsonify
from main import download_attribute_file
import pandas as pd
from io import BytesIO
from google.api_core.exceptions import GoogleAPIError
from unittest.mock import patch, MagicMock


def test_download_attribute_file_missing_department(app, mock_bigquery_client_success, mock_credentials):
    """Test missing department parameter (should return 400)"""
    with app.test_request_context('/download_attribute_file', query_string={'aisle': 'A1', 'shelf': 'S1'}):        
        response, status_code = download_attribute_file(flask.request)
        assert status_code == 400
        assert response.json['message'] == "department parameter is required"


def test_invalid_aisle_without_department(app, mock_bigquery_client_success, mock_credentials):
    with app.test_request_context('/download_attribute_file', query_string={'aisle': 'A1', 'shelf': 'S1', 'department': ''}):
        response, status_code = download_attribute_file(flask.request)
        assert status_code == 400
        print( response.json['message'] )
        assert response.json['message'] == "department parameter is required"


def test_shelf_without_aisle(app, mock_bigquery_client_success, mock_credentials):
    with app.test_request_context('/download_attribute_file', query_string={'shelf': 'S1', 'department': 'D1'}):
        response, status_code = download_attribute_file(flask.request)
        assert status_code == 400
        assert response.json['message'] == "shelf without aisle is not allowed"


@patch('google.cloud.bigquery.Client', autospec=True)
def test_no_data_for_combination(mock_client, app, mock_credentials):
    mock_query_job = MagicMock()
    mock_client.return_value.query.return_value = mock_query_job
    mock_row_iterator = MagicMock()
    mock_query_job.result.return_value = mock_row_iterator
    mock_row_iterator.to_dataframe.return_value = pd.DataFrame()


    with app.test_request_context('/download_attribute_file', query_string={'department': 'Electronics', 'aisle': 'A1', 'shelf': 'S3'}):        
        response, status_code = download_attribute_file(flask.request)
        assert status_code == 404
        assert response.json['message'] == "No data present for the selected department, aisle and shelf combination"


@patch('google.cloud.bigquery.Client', autospec=True)
@patch('pandas.DataFrame.to_excel')
def test_valid_request(mock_to_excel, mock_client, app, mock_credentials, sample_data):
    mock_query_job = MagicMock()
    mock_client.return_value.query.return_value = mock_query_job
    mock_row_iterator = MagicMock()
    mock_query_job.result.return_value = mock_row_iterator
    mock_row_iterator.to_dataframe.return_value = sample_data


    with app.test_request_context('/download_attribute_file', query_string={'department': 'Electronics', 'aisle': 'A1', 'shelf': 'S1'}):
        response = download_attribute_file(flask.request)
        assert isinstance(response, flask.Response)
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    assert mock_to_excel.call_count == 2

    args1, kwargs1 = mock_to_excel.call_args_list[0]

    file_name_1 = "Electronics_A1_S1_12032024_101139732899.xlsx"
    assert kwargs1['index'] == False
    assert 'Electronics_A1_S1' in args1[0]


@patch('google.cloud.bigquery.Client', autospec=True)
def test_bigquery_api_error(mock_client, app, mock_credentials):
    mock_client.return_value.query.side_effect = GoogleAPIError("BigQuery error")
    with app.test_request_context('/download_attribute_file', query_string={'department': 'Electronics'}):
        response, status_code = download_attribute_file(flask.request)
        assert status_code == 500
        assert response.json['message'] == "BigQuery API error: BigQuery error"


@patch('google.cloud.bigquery.Client', autospec=True)
def test_unexpected_error(mock_client, app, mock_credentials):
    mock_client.return_value.query.side_effect = Exception("Unexpected error")
    with app.test_request_context('/download_attribute_file', query_string={'department': 'Electronics'}):
        response, status_code = download_attribute_file(flask.request)
        assert status_code == 500
        assert response.json['message'] == "An error occurred: Unexpected error"
