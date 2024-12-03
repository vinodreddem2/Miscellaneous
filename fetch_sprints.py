def fetch_sprint_ids_for_pi(pi_value):
    pi_field_name = 'cf[13505]'  # Replace with your custom field for Program Increment (PI)
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