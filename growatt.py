#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from enum import IntEnum
from pprint import pprint
from sys import exit
import datetime
import hashlib
import json
import netrc
import requests

# Function to create hash for your password to login with
def hash_password(password):
    """
    Normal MD5, except add c if a byte of the digest is less than 10.
    """
    password_md5 = hashlib.md5(password.encode('utf-8')).hexdigest()
    for i in range(0, len(password_md5), 2):
        if password_md5[i] == '0':
            password_md5 = password_md5[0:i] + 'c' + password_md5[i + 1:]
    return password_md5

class Timespan(IntEnum):
    day = 1
    month = 2


class GrowattApi:
    server_url = 'https://server.growatt.com/'

    def __init__(self):
        self.session = requests.Session()

    def get_url(self, page):
        return self.server_url + page

    def login(self, username, password):
        password_md5 = hash_password(password)
        response = self.session.post(self.get_url('LoginAPI.do'), data={
            'userName': username,
            'password': password_md5
        })
        data = json.loads(response.content.decode('utf-8'))
        return data['back']

    def plant_list(self, user_id):
        response = self.session.get(self.get_url('PlantListAPI.do'),
                                    params={'userId': user_id},
                                    allow_redirects=False)
        if response.status_code != 200:
            raise RuntimeError("Request failed: %s", response)
        data = json.loads(response.content.decode('utf-8'))
        return data['back']

    def plant_detail(self, plant_id, timespan, date):
        assert timespan in Timespan
        if timespan == Timespan.day:
            date_str = date.strftime('%Y-%m-%d')
        elif timespan == Timespan.month:
            date_str = date.strftime('%Y-%m')

        response = self.session.get(self.get_url('PlantDetailAPI.do'), params={
            'plantId': plant_id,
            'type': timespan.value,
            'date': date_str
        })
        data = json.loads(response.content.decode('utf-8'))
        return data['back']


# Set username and password here
if __name__ == "__main__":
    try:
        MyNetrc = netrc.netrc()
        credentials = MyNetrc.authenticators("growat.com")
        if credentials:
            username = credentials[0] 
            password = credentials[2] 
        else:
            print("No netrc entry")
            exit(-1)
    except netrc.NetrcParseError:
        print("Unable to parse netrc")
        exit(-1)
 
    api = GrowattApi()
    login_res = api.login(username, password)
    if login_res['success'] == False:
        print("Login failed.")
        exit(-1)
    user_id = login_res['userId']
    # Get basic plant info
    plant_info = api.plant_list(user_id)

    # Get detailed plant info
    plant_id = plant_info['data'][0]['plantId']
    plant_detail = api.plant_detail(plant_id, Timespan.day, datetime.date.today())
    currentEnergy = plant_detail['plantData']['currentEnergy']
    print(currentEnergy)
    
