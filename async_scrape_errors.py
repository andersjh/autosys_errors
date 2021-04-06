from bs4 import BeautifulSoup
import requests
import pandas as pd
import asyncio
import httpx
import time
import warnings


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
    async with httpx.AsyncClient(timeout=None, verify=False) as client:
        href = msg_dict['link']
        error_key = msg_dict['key']
        response = await client.get(href, timeout=None)
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
        print(msg_index, msg_dict['key'])

async def main():
    error_msgs = get_error_list()
    print(f"We have {len(error_msgs)} to process!")

    task_list = []
    for index, msg in enumerate(error_msgs):
        task_list.append(get_error_details(index, msg))
        if index // 10 == 0:
            await asyncio.gather(*task_list)
            task_list = []
            await asyncio.sleep(.25)

    await asyncio.gather(*task_list)        
    return error_msgs

if __name__ == "__main__":
    start_time = time.monotonic()
    error_messages = asyncio.run(main())
    print("all done")
    print(error_messages[1568])
    print(f"total errors {len(error_messages)}")
    df = pd.DataFrame(error_messages)
    df.to_csv('error_msgs_async.csv', index=False)
    print(f"This took : {time.monotonic() - start_time} seconds")

    
            
