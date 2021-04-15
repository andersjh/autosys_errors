from asyncio import gather, create_task, run
import warnings
import time
from string import Template
from aiohttp import web, ClientSession
from bs4 import BeautifulSoup
import requests
import pandas as pd

def get_error_list():
    warnings.filterwarnings("ignore", message="Unverified")
    url = "https://techdocs.broadcom.com/us/en/ca-enterprise-software/intelligent-automation/autosys-workload-automation/12-0-01/messages/error-messages.html"
    # Retrieve page with the requests module
    response = requests.get(url, verify=False)
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

async def get_error_details(msg_index, msg_dict):
    async with ClientSession() as client:
        href = msg_dict['link']
        error_key = msg_dict['key']
        async with client.get(href) as resp:
            response_html = await resp.read()
            response_html = response_html.decode('utf-8')
            # now that we have the response, let's soup it up
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
            print(msg_index, error_key)
            return msg_dict


async def main():
    start_time = time.monotonic()
    error_messages = get_error_list()
    # print('error_messages:\n', error_messages)
    print(f'We found {len(error_messages)} to process..') 
    tasks = [create_task(get_error_details(k,v)) for k,v in enumerate(error_messages)]    
    await gather(*tasks)
    print(f"All done with {len(tasks)}!")
    results = [task.result() for task in tasks]
    print(results[500])
    df = pd.DataFrame(results)
    df.to_csv('autosys_messages.csv', index=False)
    end_time = time.monotonic()
    print(f'The process took {round(end_time - start_time, 2)}')
    
if __name__ == "__main__":
    run(main())   