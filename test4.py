import requests
from bs4 import BeautifulSoup
import json
import logging
import re

from constants import work_packages


confluence_pat = 'Bearer ODU1NDAzODkwNDA5OikeHjGtzRa5VlO6XWyMy/7YAw3x'

automaters_report_url = "https://confluence.auto.continental.cloud/display/VNIINDIA/Team_Automaters_Status_Report"


def get_confluence_content(base_url, space_key, page_title):
    

    search_url = f"{base_url}/rest/api/content?spaceKey={space_key}&title={page_title}&expand=body.storage,version"

    headers = {
        "Content-Type": "application/json",
        "Authorization": confluence_pat  # Ensure confluence_pat is defined elsewhere
    }
    print("search url is ", search_url)
    
    response = requests.get(search_url, headers=headers)
    if response.status_code == 200:
        search_data = response.json()
        if 'results' in search_data and len(search_data['results']) > 0:
            page_id = search_data['results'][0]['id']
            current_version = search_data['results'][0]['version']['number']
            current_content = search_data['results'][0]['body']['storage']['value'] 
            return page_id, current_version, current_content
    return None, None, None     


def update_automation_test_report(confluence_url, response):
    print(f"Getting Confluence page ID for URL: {confluence_url}")

    base_url = confluence_url.split('/display/')[0]
    page_info = confluence_url.split('/display/')[1].split('/')
    space_key = page_info[0]
    page_title = ' '.join(page_info[1:]).replace(",", "")

    print(f"Base URL: {base_url}")
    print(f"Space Key: {space_key}")
    print(f"Page Title: {page_title}")

    page_id, current_version, current_content = get_confluence_content(base_url, space_key, page_title)
    
    if current_content:
        # Parse the HTML content
        soup_uat = BeautifulSoup(current_content, 'html.parser')

        # Locate the "Continuous Testing" header
        continuous_testing_header = soup_uat.find(string="Continuous Testing")
        if continuous_testing_header:
            header_parent = continuous_testing_header.find_parent()
            table = header_parent.find_next('table')
            
            if table:
                # Loop through the rows to update values
                for index, row in enumerate(table.find_all('tr')):
                    # Skip the first two rows
                    if index < 2:
                        continue
                    columns = row.find_all('td')
                    if len(columns) > 0:
                        functionality_name = columns[0].get_text(strip=True).replace('\u200b', '').lower()
                        
                        if functionality_name in response:
                            counts = response[functionality_name]
                            existing_dev_mnl = columns[2].get_text(strip=True)
                            existing_dev_aut = columns[3].get_text(strip=True)
                            existing_uat_mnl = columns[4].get_text(strip=True)
                            existing_uat_aut = columns[5].get_text(strip=True)

                            # Update the cells with the new counts
                            columns[2].string = str(counts['dev_mnl_cnt'])
                            columns[3].string = str(counts['dev_aut_cnt'])
                            columns[4].string = str(counts['uat_mnl_cnt'])
                            columns[5].string = str(counts['uat_aut_cnt'])

                            # Update the total cell (assuming it's the first column)
                            total_value = sum([counts['dev_mnl_cnt'], counts['dev_aut_cnt'], counts['uat_mnl_cnt'], counts['uat_aut_cnt']])
                            columns[1].string = str(total_value)
                            functionality_cell = columns[0] 
                            # Change background color to green if values updated
                            if (columns[2].string != existing_dev_mnl or
                                columns[3].string != existing_dev_aut or
                                columns[4].string != existing_uat_mnl or
                                columns[5].string != existing_uat_aut):
                                functionality_cell['style'] = 'background-color: green;'
                            else:
                                del functionality_cell['style']

                # Convert updated HTML back to a string
                new_content = str(soup_uat)

                update_data = {
                    "id": page_id,
                    "type": "page",
                    "version": {
                        "number": current_version + 1
                    },
                    "title": page_title,
                    "body": {
                        "storage": {
                            "value": new_content,
                            "representation": "storage"
                        }
                    }
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": confluence_pat  # Ensure confluence_pat is defined elsewhere
                }
                
                # Update the Confluence page
                response = requests.put(f"{base_url}/rest/api/content/{page_id}", headers=headers, data=json.dumps(update_data))
                if response.status_code == 200:
                    print("Page updated successfully.")
                else:
                    print("Failed to update page:", response.content)
            else:
                print("No table found under 'Continuous Testing'.")            
        else:
            print("Continuous Testing header not found.")


def get_confluence_page_info(confluence_url):
    print(f"Getting Confluence page ID for URL: {confluence_url}")
    
    base_url = confluence_url.split('/display/')[0]
    page_info = confluence_url.split('/display/')[1].split('/')
    space_key = page_info[0]
    page_title = ' '.join(page_info[1:]).replace(",","")
    
    print(f"Base URL: {base_url}")
    print(f"Space Key: {space_key}")
    print(f"Page Title: {page_title}")

    page_id, current_version, current_content = get_confluence_content(base_url, space_key, page_title)
    return base_url, page_id, current_version, current_content, page_title

    
def count_rows_in_first_table(table):
    if not table:
        logging.error("First table not found!")
        return 0, 0, 0

    manual_count = 0
    automated_count = 0
    total_count = 0
    keyword_row_start_index = 5  

    rows = table.find_all('tr')
    
    if not rows:
        logging.error("No rows found in the first table!")
        return 0, 0, 0
    
    for index, row in enumerate(rows[keyword_row_start_index:]):
        import pdb
        pdb.set_trace()

        
        td_cells = row.find_all('td')
        th_cells =row.find_all('th')
        if not td_cells and th_cells:
            continue
        

        row_text = ' '.join(cell.text.strip() for cell in td_cells+th_cells)
        print("row_text is ", row_text)
        if not row_text.strip():
            print(f"Skipping row {index + keyword_row_start_index} because it's empty (no content)")
            continue 

        print(f"Row {index} content: {row_text}")
        if 'Negative / Exception Testing' in row_text or 'Other Non-Functional Testing' in row_text or 'Feature / Module/ Pipeline Testing' in row_text:
            print(f"Skipping row {index + keyword_row_start_index} due to excluded content")
            continue
       
        if re.search(r'\bmanual\b', row_text, re.IGNORECASE):
            
            manual_count += 1
            # total_count += 1
            # continue
            print("Its a manual Row -- Current Manual Row is ", manual_count)
        if re.search(r'\bautomated\b', row_text, re.IGNORECASE):
            automated_count += 1
            print("Its a Auomated Row -- Current Auomated Row is ", manual_count)
        total_count += 1       

    return manual_count, automated_count, total_count


def update_confluence_page(work_package):
    manual_count_dev, automated_count_dev, total_count_dev = None, None, None
    manual_count_uat, automated_count_uat, total_count_uat = None, None, None
    dev_url = work_package['dev']    
    # base_url, dev_page_id, dev_current_version, dev_content, dev_page_title = get_confluence_page_info(dev_url)
    
    # if not dev_page_id:
    #     logging.error(f"Could not retrieve Source Test page ID or content for given url {dev_url}")
    # else:
    #     # Parse the Dev page content to find the first table and count rows
    #     soup_dev = BeautifulSoup(dev_content, 'html.parser')
    #     all_tables = soup_dev.find_all('table')

    #     print("Dev tables are ", all_tables)
    #     if not all_tables:
    #         logging.error("No tables found in the Dev page content!")

    #     manual_count_dev, automated_count_dev, total_count_dev = count_rows_in_first_table(all_tables[0])
        
       # Handle UAT URL
    uat_url = work_package['uat']
    base_url, uat_page_id, uat_current_version, uat_content, uat_page_title = get_confluence_page_info(uat_url)

    if not uat_page_id:
        logging.error(f"Could not retrieve UAT page ID or content for given url {uat_url}")
    else:
        # Parse the UAT page content to find the first table and count rows
        soup_uat = BeautifulSoup(uat_content, 'html.parser')
        all_uat_tables = soup_uat.find_all('table')

        if not all_uat_tables or len(all_uat_tables)<2:
            logging.error("No tables found in the UAT page content to update test content!")
            return
        print("UAT tables are ", all_uat_tables)
        if not all_uat_tables:
            logging.error("No tables found in the UAT page content!")
        else:
            manual_count_uat, automated_count_uat, total_count_uat = count_rows_in_first_table(all_uat_tables[0])

        second_table = all_uat_tables[1]
        print(manual_count_uat, automated_count_uat, total_count_uat)
        rows = second_table.find_all('tr')

            # Check if the counts are not None before updating
        if len(rows) > 2:  # Ensure there are enough rows
            # Update Dev row
            if manual_count_dev is not None and automated_count_dev is not None:
                update_row_dev = rows[1]
                update_cells_dev = update_row_dev.find_all('th')

                if len(update_cells_dev) >= 4:
                    update_cells_dev[1].string = str(total_count_dev)  # Total count
                    update_cells_dev[2].string = str(automated_count_dev)  # Automated count
                    update_cells_dev[3].string = str(manual_count_dev)  # Manual count
                else:
                    logging.error("Dev Test row not found in the UAT page table!")

            # Update UAT row
            if manual_count_uat is not None and automated_count_uat is not None:
                update_row_uat = rows[2]
                update_cells_uat = update_row_uat.find_all('th')

                if len(update_cells_uat) >= 4:
                    update_cells_uat[1].string = str(total_count_uat)  # Total count
                    update_cells_uat[2].string = str(automated_count_uat)  # Automated count
                    update_cells_uat[3].string = str(manual_count_uat)  # Manual count
                else:
                    logging.error("UAT Test row not found in the UAT page table!")
            if len(rows) > 3:  # Ensure there are enough rows for total
                 total_row_count = rows[3]
                 total_row_cells = total_row_count.find_all('th')

                 if len(total_row_cells) >= 4:
                    total_dev_count = (total_count_dev if total_count_dev is not None else 0)
                    total_uat_count = (total_count_uat if total_count_uat is not None else 0)
                    total_row_cells[1].string = str(total_dev_count + total_uat_count)
                    total_row_cells[2].string = str((automated_count_uat if automated_count_uat is not None else 0) + (automated_count_dev if automated_count_dev is not None else 0))  # Automated count
                    total_row_cells[3].string = str((manual_count_uat if manual_count_uat is not None else 0) + (manual_count_dev if manual_count_dev is not None else 0))  # Manual count


        # Convert updated HTML back to a string
        new_content = str(soup_uat)
    
        update_data = {
            "id": uat_page_id,
            "type": "page",
            "version": {
                "number": uat_current_version + 1
            },
            "title": uat_page_title,
            "body": {
                "storage": {
                    "value": new_content,
                    "representation": "storage"
                }
            }
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": confluence_pat
        }
        # response = requests.put(f"{base_url}/rest/api/content/{uat_page_id}", headers=headers, data=json.dumps(update_data))
        # if response.status_code == 200:
        #     logging.info(f"Confluence page updated successfully with new counts.")
        # else:
        #     logging.error(f"Failed to update Confluence page. Status code: {response.status_code}")
        #     logging.error(f"Response content: {response.text}")

    # Prepare output counts
    test_count = {
        'functionality': work_package['functionality'],
        'dev_mnl_cnt': manual_count_dev if manual_count_dev else 0,
        'dev_aut_cnt': automated_count_dev if automated_count_dev else 0,
        'uat_mnl_cnt': manual_count_uat if manual_count_uat else 0,
        'uat_aut_cnt': automated_count_uat if automated_count_uat else 0
    }
        
    return test_count

# Example usage
dev_page_url = 'https://confluence.auto.continental.cloud/display/VWE3ICAS1/01_Developement_Testing_WP14'
uat_page_url = 'https://confluence.auto.continental.cloud/display/VWE3ICAS1/02_User_Acceptance_Testing_WP14'
confluence_pat = 'Bearer OTcyNDI1ODQ3MzE4OubnhRfA6w1LaQZgBXCv55eSvS5U'

if __name__ == "__main__":
    response = {}
    for wp in work_packages:                
        res_cnt =  update_confluence_page(wp)
        if res_cnt:
            response[wp['functionality']] = res_cnt

    
    # update_automation_test_report(automaters_report_url, response)