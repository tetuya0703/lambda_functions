from typing import List, Dict, Optional
import urllib.request
import re
import json
import os


class UserList:
    def __init__(self):
        self.__users = {}
        self.__user_synonyms = {}

    def get_user_id(self, username: str) -> Optional[str]:
        if not self.__users:
            self.__download_user_list()
        primary_result = self.__users.get(username.lower())
        if primary_result is None:
            return self.__user_synonyms.get(username.lower())
        else:
            return primary_result

    def __download_user_list(self):
        token = 'xoxp-2355026419-653504213222-984822269556-b42167a99cb0cf06e3efbcbea8be9a65'
        url = f'https://slack.com/api/users.list?token={token}'
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as res:
            members = json.loads(res.read())['members']

        split_ptn = re.compile(r'\.| ')
        for m in members:
            names = set([m['name'].lower(),
                         m['profile']['display_name'].lower(),
                         m['profile']['display_name_normalized'].lower()])
            synonyms = set()
            for n in names:
                self.__users[n] = m['id']
                partials = split_ptn.split(n)
                for p in partials:
                    if p not in names:
                        synonyms.add(p)
                joined = ''.join(partials)
                if joined not in names:
                    synonyms.add(joined)

            for s in synonyms:
                self.__user_synonyms[s] = m['id']


def send_slack(channel: str, text: str,
               attachments: List[Dict] = []) -> None:
    headers = {
        'Content-Type': 'application/json',
    }
    webhook_base_url = 'https://hooks.slack.com/services/T02AF0SCB/'
    channels = {
        'iiso_all': 'BUZ940005/AZF2nAAY6hlu45A9hYWP3Ivt',
        'iiso_jp': 'BV974TAMC/ylkTQJdIuT6ZHGi4ROMDrpsm',
        'sagemaker_monitor': 'BV6H21KE0/l58IToPEinCggFQ1GkJ3KA7P',
        'it_aws_instance_req': 'BUVGQ86NP/bDEHVC8UoFCPGdl1NMA1yJeV',
    }
    if channel in channels:
        channel_path = channels[channel]
    else:
        channel_path = channels['iiso_all']
        text = 'ADD CHANNEL PATH TO "send_slack" METHOD IN Lambda Layer\n' + text

    url = os.path.join(webhook_base_url, channel_path)

    payload = {
        'text': text,
        'attachments': attachments,
    }
    req = urllib.request.Request(url,
                                 json.dumps(payload).encode(),
                                 headers)
    urllib.request.urlopen(req)


# debug

# send_slack('iiso_jp', 'text',
#     [{'color': 'good', 'fields': [{'title': 't', 'value': 'v', 'short': False}]}])
# ul = UserList()
# print(ul.get_user_id('Jeff'))
# print(ul.get_user_id('van'))
# print(ul.get_user_id('le'))
# print(ul.get_user_id('ken'))
# print(ul.get_user_id('ken maeda'))
