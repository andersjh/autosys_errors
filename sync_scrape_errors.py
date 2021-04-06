
# Dependencies
from bs4 import BeautifulSoup
import requests
import pandas as pd
import time

start_time = time.monotonic()

def get_error_list():
    url = "https://techdocs.broadcom.com/us/en/ca-enterprise-software/intelligent-automation/autosys-workload-automation/12-0-01/messages/error-messages.html"
    # Retrieve page with the requests module
    response = requests.get(url)
    # Create BeautifulSoup object; parse with 'html.parser'
    soup = BeautifulSoup(response.text, 'html.parser')
    error_msgs = []

    links = soup.find_all('a', class_="link")
    for cur_link in links:
        error_key = cur_link.find('div')
        if error_key.text and error_key.text.startswith('CAU'):
            error_msgs.append({
                'key': error_key.text,
                'message': cur_link['title'],
                'link': f"https://techdocs.broadcom.com{cur_link['href']}",
                'reason': '',
                'action': ''
            })

    return error_msgs


        
def get_error_details(msg_index, msg_dict):
    href = msg_dict['link']
    error_key = msg_dict['key']
    response = requests.get(href)
    response_html = response.text

    error_soup = BeautifulSoup(response_html, 'html.parser')
    info = error_soup.find_all('div', class_="div")
    if info:
        info_divs = info[0].find_all('div', class_="p")
        this_reason = False
        this_action = False
        for i in info_divs:
            bold_found = i.find('b')
            if this_reason:
                this_reason = False
                msg_dict['reason'] = i.find('div').text
            elif this_action:
                cur_action = i.find('div').text
                if cur_action == "Required action unknown.":
                    cur_action = ""
                msg_dict['action'] = cur_action  
                this_action = False
            if bold_found:
                bold_text = bold_found.find('div').text
                if bold_text == "Reason:":
                    this_reason = True
                elif bold_text == "Action:":
                    this_action = True
    # print(msg_index, ['key'])

def main():
    error_msgs = get_error_list()

    for cur_index, cur_msg in enumerate(error_msgs):
        print(cur_index, cur_msg['key'])
        get_error_details(cur_index, cur_msg)      

    df = pd.DataFrame(error_msgs)

    df.to_csv('error_msgs.csv', index=False)
    print("All done")
    print(f"This took {time.monotonic() - start_time} seconds")

if __name__ == "__main__":
    main()




