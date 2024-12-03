import functions_framework
from flask import Flask, jsonify, request, make_response
import pandas as pd
import io
import os
import xlsxwriter
from datetime import datetime
import pytz
from google.oauth2 import service_account
from google.cloud import bigquery, storage
import logging
from google.api_core.exceptions import GoogleAPIError

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)


@functions_framework.http
def download_attribute_file(request):
    """Downloads an XLSX file containing department, aisle, and shelf data."""
    try:
        env = os.getenv('config', 'local')  # 'default_value' is optional and used if 'config' is not set
        print("config set: " + env)
        gcs_bucket = ""
        if env != 'local':
            gcs_bucket = f'occg-catalog-{env}-bkt-01'
            print("Reading the configuration file from Google cloud")
            cloud_storage_client = storage.Client()
            bucket = cloud_storage_client.bucket(gcs_bucket)
            blob_service_account = bucket.blob(f'environment-properties/{env}-service-account.json')
            blob_service_account.download_to_filename(f"{env}-service-account.json")
            credentials = service_account.Credentials.from_service_account_file(f"{env}-service-account.json")
            project_id = f"gcp-abs-occg-{env}-prj-01"
        else:
            credentials = service_account.Credentials.from_service_account_file(
                "service-account/dev-service-account.json")
            project_id = "gcp-abs-occg-dev-prj-01"
        bigquery_client = bigquery.Client(credentials=credentials, project=project_id)

        current_time = datetime.now(pytz.timezone('US/Pacific')).strftime("%m%d%Y_%H%M%S%f")
        department = request.args.get('department')
        aisle = request.args.get('aisle', '')
        shelf = request.args.get('shelf', '')

        if not department:
            return jsonify({'message': "department parameter is required"}), 400
        elif aisle!='' and department == '':
            return jsonify({'message': "Department shouldn't be null when aisle is present"}), 400
        elif aisle == '' and shelf != '':
            return jsonify({'message': "shelf without aisle is not allowed"}), 400

        base_query = f"SELECT * FROM `{project_id}.occg_ds_catalog_enrichment.dynamic_attributes` WHERE raw_data IS NULL"
        query_params = []

        if department.lower() == 'all':
            query = base_query
        else:
            if not department:
                raise ValueError("Department must be specified if aisle or shelf is present.")

            query = f"{base_query} AND department_name = @department"
            query_params.append(bigquery.ScalarQueryParameter('department', 'STRING', department))

            if aisle:
                if aisle.lower() == 'all':
                    query = f"{base_query} AND department_name = @department"
                else:
                    query += " AND aisle_name = @aisle"
                    query_params.append(bigquery.ScalarQueryParameter('aisle', 'STRING', aisle))

            if shelf:
                if not aisle:
                    raise ValueError("Aisle must be specified if shelf is present.")

                if shelf.lower() == 'all':
                    query = f"{base_query} AND department_name = @department AND aisle_name = @aisle"
                else:
                    query += " AND shelf_name = @shelf"
                    query_params.append(bigquery.ScalarQueryParameter('shelf', 'STRING', shelf))

        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        print(query)
        dynamic_attributes = bigquery_client.query(query, job_config=job_config).result().to_dataframe()
        if len(dynamic_attributes) == 0:
            return jsonify({"message": "No data present for the selected department, aisle and shelf combination"}), 404

        final_df = construct_final_df(dynamic_attributes)
        file_name = "_".join(filter(None, [department, aisle, shelf])).replace(" ", "") + "_" + current_time
        if env == 'local':
            gcs_generated_file_path = f"downloaded-files/{file_name}.xlsx"
        else:
            gcs_generated_file_path = f"gs://{gcs_bucket}/dynamic-attributes/ui-download-files/downloaded-files/{file_name}.xlsx"
        final_df.to_excel(gcs_generated_file_path, index=False)
        print(final_df)
        # dynamic_attributes = bigquery_client.query(query).to_dataframe()
        # # print(dynamic_attributes)
        # # print("Fetched data from big query")
        # data = {"department": [department], "aisle": [aisle], "shelf": [shelf]}
        # dynamic_attributes = pd.DataFrame(data)
        if not final_df.empty:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                final_df.to_excel(writer, sheet_name='GeneratedAttributes', index=False)
            output.seek(0)

            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            response.headers['Content-Disposition'] = f'attachment; filename={file_name}.xlsx'
            response.headers['Content-Length'] = str(len(output.getvalue()))
            logging.info(f"Downloaded file: {file_name}.xlsx")
            return response
        else:
            return jsonify({"message": "Not able to read data from bigquery"}), 400

    except GoogleAPIError as e:
        logging.exception(f"BigQuery API error: {e}")
        return jsonify({'message': f'BigQuery API error: {str(e)}'}), 500
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
        return jsonify({'message': f'An error occurred: {str(e)}'}), 500


def construct_final_df(dynamic_attributes):
    if len(dynamic_attributes) > 0:
        dynamic_attributes_business = dynamic_attributes[dynamic_attributes["attribute_type"] == 'business']
        dynamic_attributes_group = dynamic_attributes.groupby(['department_name', 'aisle_name', 'shelf_name'])
        max_version = dynamic_attributes_group['version'].max()
        version_data = max_version.reset_index()
        print("vinod version_data is ", version_data)
        print(dynamic_attributes_business[['department_name', 'attribute_type']])
        dynamic_attributes_max_version = dynamic_attributes.merge(version_data,
                                                                  on=['department_name', 'aisle_name',
                                                                      'shelf_name', 'version'], how='inner')
        print(dynamic_attributes_max_version[['department_name', 'attribute_type']])
        dynamic_attributes_final = pd.concat([dynamic_attributes_max_version, dynamic_attributes_business],
                                             ignore_index=True)
        print(dynamic_attributes_final[['department_name', 'attribute_type']])
        dynamic_attributes_final = dynamic_attributes_final[['department_name', 'aisle_name', 'shelf_name', 'attribute',
                                                             'possible_values', 'attribute_type', 'review',
                                                             'similar_attributes']]
        
        dynamic_attributes_final = dynamic_attributes_final.drop_duplicates()
        return dynamic_attributes_final
    else:
        return pd.DataFrame()
