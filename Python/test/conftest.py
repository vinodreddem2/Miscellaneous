import pytest
import pandas as pd
from unittest import mock
from flask import Flask, jsonify
from google.auth.credentials import AnonymousCredentials
from main import download_attribute_file
from google.cloud import bigquery
from unittest.mock import MagicMock

@pytest.fixture
def app():
    """Create and configure a Flask app instance for testing."""
    app = Flask(__name__)
    # Register the route to the app for testing
    app.add_url_rule('/download_attribute_file', 'download_attribute_file', download_attribute_file, methods=['GET'])
    return app


@pytest.fixture
def sample_data():
    """Fixture that provides sample data for tests."""
    return pd.DataFrame({
        'department_name': ['Electronics', 'Electronics', 'Electronics', 'Clothing'],
        'aisle_name': ['A1', 'A1', 'A2', 'C1'],
        'shelf_name': ['S1', 'S2', 'S1', 'S1'],
        'attribute': ['Attribute1', 'Attribute2', 'Attribute3', 'Attribute4'],
        'possible_values': ['Value1', 'Value2', 'Value3', 'Value4'],
        'attribute_type': ['business', 'technical', 'business', 'business'],
        'review': ['Reviewed', 'Pending', 'Reviewed', 'Pending'],
        'similar_attributes': ['Attr1', 'Attr2', 'Attr3', 'Attr4'],
        'version': [1, 1, 2, 1]
    })

@pytest.fixture
def mock_bigquery_client_success(mocker, sample_data):
    mock_client = mock.Mock()
    mock_query_job = mock.Mock()
    mock_query_job.result.return_value.to_dataframe.return_value = sample_data  # Simulate returned data
    mock_client.query.return_value = mock_query_job
    return mock_client

@pytest.fixture
def mock_bigquery_client_empty(mocker):    
    mock_client = MagicMock(spec= bigquery.Client)
    mock_query_job = MagicMock()
    mock_query_job.to_dataframe.return_value = pd.DataFrame()
    mock_client.query.return_value = mock_query_job
    return mock_client

@pytest.fixture
def mock_bigquery_client_error(mocker):
    mock_client = mock.Mock()
    mock_query_job = mock.Mock()
    mock_query_job.result.side_effect = Exception("BigQuery query failed")
    mock_client.query.return_value = mock_query_job
    return mock_client

@pytest.fixture
def mock_gcs_client(mocker):
    mock_storage_client = mock.Mock()
    mock_bucket = mock.Mock()
    mock_blob = mock.Mock()
    mock_storage_client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob
    return mock_storage_client

@pytest.fixture
def mock_credentials(mocker):
    mock_creds = mock.Mock(spec=AnonymousCredentials)  # Using AnonymousCredentials as an acceptable mock
    mock_creds.token = "mock-token"  # Simulating a valid token
    mocker.patch('google.oauth2.service_account.Credentials.from_service_account_file', return_value=mock_creds)
    return mock_creds

@pytest.fixture
def mock_datetime_now(mocker):
    mock_datetime = mock.Mock()
    mock_datetime.now.return_value.strftime.return_value = "12122024_120000000000"
    mocker.patch('datetime.datetime', mock_datetime)  # Replace datetime.datetime with the mock
    return mock_datetime

# pip install pytest
# pip install pytest pytest-mock
# pip install google-cloud-bigquery
# pip install google-cloud-storage
# pip install pandas
# pip install xlsxwriter
# pip install functions-framework
# pip install google-auth
# pip install google-auth-oauthlib
# pip install pytz
# pip install Flask
# pip install requests
