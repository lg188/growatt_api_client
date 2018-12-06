#!/usr/bin/env python3
"""
A client for the Growatt API
"""

from enum import IntEnum
import sys
import datetime
import hashlib
import json
import netrc as Netrc
import time as Time
import requests


# Function to create hash for your password to login with
def hash_password(password_raw):
    """
    Normal MD5, except add c if a byte of the digest is less than 10.
    """
    password_md5 = hashlib.md5(password_raw.encode('utf-8')).hexdigest()
    for i in range(0, len(password_md5), 2):
        if password_md5[i] == '0':
            password_md5 = password_md5[0:i] + 'c' + password_md5[i + 1:]
    return password_md5


class Timespan(IntEnum):
    """
    The timespans supported by the Growatt API.
    """
    now = 0
    day = 1
    month = 2
    year = 3


class GrowattApi:
    """
    A collection of all known API calls for the API.
    """

    server_url = 'https://server.growatt.com/'

    def __init__(self):
        self.session = requests.Session()

    def get_url(self, page):
        """
        A helper function to parse URLs.
        """
        return self.server_url + page

    def login(self, user, raw_password):
        """
        Log in on the API.
        """
        password_md5 = hash_password(raw_password)
        response = self.session.post(self.get_url('LoginAPI.do'), data={
            'userName': user,
            'password': password_md5
        })
        data = json.loads(response.content.decode('utf-8'))
        return data['back']

    def plant_list(self, user_id):
        """
        Retrieve the list of all plants.
        """
        response = self.session.get(self.get_url('PlantListAPI.do'),
                                    params={'userId': user_id},
                                    allow_redirects=False)
        if response.status_code != 200:
            raise RuntimeError(f"Request failed: {response}")
        data = json.loads(response.content.decode('utf-8'))
        return data['back']

    def plant_detail(self, plant_id, timespan, time):
        """
        Retrieves the metric data of a plant.
        Based on the timespan
        """
        assert timespan in Timespan
        if timespan == Timespan.now:
            time_str = Time.time()
        elif timespan == Timespan.day:
            time_str = time.strftime('%Y-%m-%d')
        elif timespan == Timespan.month:
            time_str = time.strftime('%Y-%m')
        elif timespan == Timespan.year:
            time_str = time.strftime('%Y')

        response = self.session.get(self.get_url('PlantDetailAPI.do'), params={
            'plantId': plant_id,
            'type': timespan.value,
            'date': time_str
        })
        data = json.loads(response.content.decode('utf-8'))
        return data['back']


# Set username and password here
if __name__ == "__main__":
    sys.tracebacklimit = 0
    try:
        NETRC = Netrc.netrc()
        CREDENTIALS = NETRC.authenticators("growat.com")
        if CREDENTIALS:
            USERNAME = CREDENTIALS[0]
            PASSWORD = CREDENTIALS[2]
        else:
            raise RuntimeError("Netrc entry missing")
    except NETRC.NetrcParseError as err:
        raise RuntimeError(f"Could not parse the netrc file: {err}")

    API = GrowattApi()

    LOGIN = API.login(USERNAME, PASSWORD)
    if not LOGIN['success']:
        raise RuntimeError("Login failed")

    USER_ID = LOGIN['userId']

    # Get basic plant info
    PLANT_INFO = API.plant_list(USER_ID)

    # Get detailed plant info
    PLANT_ID = PLANT_INFO['data'][0]['plantId']
    PLANT_DETAIL = API.plant_detail(
        PLANT_ID, Timespan.day, datetime.datetime.now())
    if not PLANT_DETAIL['success']:
        if PLANT_DETAIL['errCode'] == '201':
            raise RuntimeError("The date string is invalied.")
        raise RuntimeError("The request returned invalid data.")
    CURRENT_ENERGY = PLANT_DETAIL['plantData']['currentEnergy']
    print(CURRENT_ENERGY)
