# -*- coding: utf-8 -*-

from enum import IntEnum
import datetime
import hashlib
import json
import requests
#from pprint import pprint

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
    server_url = 'http://server.growatt.com/'

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
    username = 'YourUsername'
    password = 'YourPassword'

 
    api = GrowattApi()
    login_res = api.login(username, password)
    user_id = login_res['userId']
    # Get basic plant info
    plant_info = api.plant_list(user_id)
    #pprint(plant_info)

    # Get detailed plant info
    plant_id = plant_info['data'][0]['plantId']
    plant_detail = api.plant_detail(plant_id, Timespan.day, datetime.date.today())
    #pprint(plant_detail)

    
# Prepare data for Telegram
    basic_data = plant_info['data']
    for lijst_basic in basic_data[:1]:
        todayEnergy = lijst_basic['todayEnergy']
        totalEnergy = lijst_basic['totalEnergy']
    
    basic_data2 = plant_info['totalData']
    totalMoney = basic_data2['eTotalMoneyText']
    CO2 = basic_data2['CO2Sum']
        
    detail_data = plant_detail['plantData']
    todayMoney = detail_data['plantMoneyText']
    
# Send data to Telegram
apikey = 'botXXXXXX:XXXXXXXX'
chatid = 'XXXXXXXX'
r = requests.post('https://api.telegram.org/'
                  '{}/'
                  'sendMessage?chat_id={}&'
                  'parse_mode=markdown&'
                  'text=☀ *Dagelijks Overzicht Zonnepanelen* ☀ \n'
                  'Vandaag opgewekt:        {} 🔌\n'
                  'Vandaag bespaard:         {} 💰\n'
                  '*=============================* \n'
                  'Totaal opgewekt:             {} 🔌\n'
                  'Totaal bespaard:              {} 💰\n'
                  'Totale CO2 besparing:    {} 🌱\n'.format(apikey, chatid, todayEnergy, todayMoney, totalEnergy, totalMoney, CO2))
