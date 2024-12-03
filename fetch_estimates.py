import requests
import argparse
import logging
import json
import pandas as pd

logging.basicConfig(level=logging.DEBUG)

def fetch_sprint_ids_for_pi(pi_value):
    pi_field_name = 'labels'  # Replace with your custom field for Program Increment (PI)
    jira_base_url = 'https://jira-ibs.zone2.agileci.conti.de'
    url = f"{jira_base_url}/rest/api/2/search"

    with open('config.json') as config_file:
        config_data = json.load(config_file)
        API_KEY = config_data.get('API_KEY', '')

    headers = {
        "Accept": "application/json",
        'Content-Type': 'application/json',
        "Authorization": f"Bearer {API_KEY}"
    }

    # JQL query to fetch all issues associated with the given PI
    jql_query = f'"{pi_field_name}" = "{pi_value}"'

    start_at = 0
    max_results = 50
    total_results = 1  # Set initially to enter the loop
    sprint_ids = set()  # To store unique Sprint IDs

    while start_at < total_results:
        # Add pagination support to iterate through results
        params = {
            'jql': jql_query,
            'startAt': start_at,
            'maxResults': max_results,
            'fields': 'sprint',  # Only retrieve the sprint field
        }
        response = requests.get(url, headers=headers, params=params)
        logging.debug(f"Request URL: {response.url}")
        
        if response.status_code == 200:
            data = response.json()
            print(data)

def fetch_estimates_and_time_spent(issue_type, responsible_team, sprint_id):
    custom_field_clause_name = 'cf[13504]'  # Replace with your custom field
    jira_base_url = 'https://jira-ibs.zone2.agileci.conti.de'
    url = f"{jira_base_url}/rest/api/2/search"

    with open('config.json') as config_file:
        config_data = json.load(config_file)
        API_KEY = config_data.get('API_KEY', '')
    
    headers = {
        "Accept": "application/json",
        'Content-Type': 'application/json',
        "Authorization": API_KEY
    }
    
    # JQL query to fetch issues based on issue type, team, and sprint
    #jql_query = f'issuetype = "{issue_type}" AND "{custom_field_clause_name}" = "{responsible_team}" AND Sprint = {sprint_id}'
    pi_value ="PIPE24.24"
    jql_query = f'labels = "{pi_value}" AND issuetype = "{issue_type}" AND "{custom_field_clause_name}" = "{responsible_team}"'
    
    start_at = 0
    max_results = 50
    total_results = 1  # Set initially to enter the loop
    team_data = {}

    # Loop through paginated results
    while start_at < total_results:
        params = {
            "jql": jql_query,
            "fields": "customfield_10004",
            "startAt": start_at,
            "maxResults": max_results
        }
        
        response = requests.get(url, headers=headers, params=params)
        logging.debug(f"Request URL: {response.url}")
        print("response",response.status_code)
        print("responsejson",response.json())
        with open('jira_response.json','w') as f :
            json.dump(response.json(),f,indent=4)
        break

    #     if response.status_code == 200:
    #         data = response.json()
    #         total_results = data['total']  # Total number of issues matching the query
    #         issues = data.get('issues', [])

    #         if not issues and start_at == 0:
    #             logging.error("No issues found matching the JQL query.")
    #             return []
            
    #         # Process each issue
    #         for issue in issues:
    #             assignee = issue['fields']['assignee']['displayName'] if issue['fields']['assignee'] else "Unassigned"
    #             original_estimate = issue['fields'].get('timeoriginalestimate', 0)  # Time in seconds
    #             time_spent = issue['fields'].get('timespent', 0)  # Time in seconds
                
    #             # Convert time from seconds to story points (assuming 8 hours per day)
    #             original_estimate_sp = original_estimate / 60 / 60 / 8 if original_estimate else 0
    #             time_spent_sp = time_spent / 60 / 60 / 8 if time_spent else 0
                
    #             if assignee not in team_data:
    #                 team_data[assignee] = {'total_estimate': 0, 'total_time_spent': 0}
                
    #             team_data[assignee]['total_estimate'] += original_estimate_sp
    #             team_data[assignee]['total_time_spent'] += time_spent_sp
            
    #         # Update startAt to fetch the next set of results
    #         start_at += max_results
    #     else:
    #         logging.error(f"Failed to fetch tickets. Status code: {response.status_code}")
    #         logging.error(f"Response content: {response.text}")
    #         return []
    
    # # Convert dictionary to a list of lists for easier DataFrame creation
    # team_data_list = [[member, round(data['total_estimate'], 2), round(data['total_time_spent'], 2)] for member, data in team_data.items()]
    
    # return team_data_list

def print_estimates_table(team_data):
    # Create a DataFrame for the table
    df = pd.DataFrame(team_data, columns=['Team Member', 'Original Estimate (SP)', 'Time Spent (SP)'])
    
    # Print the DataFrame
    print(df)
    
    # Save the table as an HTML file
    html_content = df.to_html(index=False)
    
    # Write the HTML to a file
    with open('sprint_estimates.html', 'w') as f:
        f.write(html_content)
    
    logging.info("Estimates table saved as sprint_estimates.html")

def main():
    parser = argparse.ArgumentParser(description="Fetch Jira estimates and time spent for each team member.")
    parser.add_argument('--issue_type', help="Issue type (e.g., Sub-task)", required=True)
    parser.add_argument('--responsible_team', help="Responsible SAFe Team", required=True)
    parser.add_argument('--sprint_id', help="Sprint ID", required=True)
    
    args = parser.parse_args()

    # Fetch estimates and time spent from Jira
    team_data = fetch_estimates_and_time_spent(args.issue_type, args.responsible_team, args.sprint_id)
    
    if team_data:
        # Print the data as a table
        print_estimates_table(team_data)

if __name__ == "__main__":
    # main()
#    fetch_sprint_ids_for_pi("PIPE24.24")
     fetch_estimates_and_time_spent("task","Automaters","40221")