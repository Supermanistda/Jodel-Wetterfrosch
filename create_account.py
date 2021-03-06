import json
import jodel_api
import requests
from operator import itemgetter
from builtins import input
from ftplib import FTP

class InputJodelAcc(object):
    def __init__(self, lat=None, lng=None, city=None, access_token=None, expiration_date=None, refresh_token=None, distinct_id=None, device_uid=None, legacy=None):
        self.access_token = access_token
        self.expiration_date = expiration_date
        self.refresh_token = refresh_token
        self.distinct_id = distinct_id
        self.device_uid = device_uid
        self.lat = lat
        self.lng = lng
        self.city = city
        self.legacy = legacy

class InputWeather(object):
    def __init__(self, API_KEY, CITY_code, dwdname, dwdpass):
        self.API_KEY = API_KEY
        self.CITY = CITY_code
        self.dwdname = dwdname
        self.dwdpass = dwdpass

def y_n(question):
    answer = ""
    x = 0
    while not answer == "y" and not answer =="n":
        if x == 0:
            answer = input("%s (y/n)\n" % question)
            x = 1
        else:
            print("Invalid Input")
            answer = input("%s (y/n)\n" % question)
    if answer == "y":
        return True
    if answer =="n":
        return False

def write_data(file_data, filename):
    if ".json" not in filename:
        filename = "%s.json" % (filename)
    with open(filename, 'w') as outfile:
        json.dump(file_data, outfile, indent=4)

def create_data():
    data_jodel = get_data_Jodel()
    data_weather = get_data_Weather()
    file_data = {
        "lat":data_jodel.lat,
        "lng":data_jodel.lng,
        "city":data_jodel.city,
        "API_KEY":data_weather.API_KEY,
        "CITY":data_weather.CITY,
        "expiration_date":data_jodel.expiration_date,
        "distinct_id":data_jodel.distinct_id,
        "refresh_token":data_jodel.refresh_token,
        "device_uid":data_jodel.device_uid,
        "access_token":data_jodel.access_token,
        "legacy":data_jodel.legacy,
        "dwdname":data_weather.dwdname,
        "dwdpass":data_weather.dwdpass
        }
    return file_data

def get_data_Jodel():
    Jodels_loc = get_Jodels_loc()
    if y_n("Do you already have data for a valid Jodel account?"):
        print("Input the data for your Jodel account:\n")
        legacy = y_n("Is the account a legacy (pre Jodel 4.48) account?")
        access_token = input("Access Token:\n")
        expiration_date = int(input("Expiration Date:\n"))
        refresh_token = input("Refresh Token:\n")
        distinct_id = input("Distinct ID:\n")
        device_uid = input("Device UID:\n")
        return InputJodelAcc(access_token=access_token, expiration_date=expiration_date, refresh_token=refresh_token, distinct_id=distinct_id, device_uid=device_uid,lat=Jodels_loc.lat,lng=Jodels_loc.lng,city=Jodels_loc.city, legacy=legacy)
    Jodel_account = create_account(Jodels_loc.lat, Jodels_loc.lng, Jodels_loc.city)
    return InputJodelAcc(access_token=Jodel_account.access_token, expiration_date=Jodel_account.expiration_date, refresh_token=Jodel_account.refresh_token, distinct_id=Jodel_account.distinct_id, device_uid=Jodel_account.device_uid,lat=Jodels_loc.lat,lng=Jodels_loc.lng,city=Jodels_loc.city, legacy=Jodel_account.legacy)

def create_account(lat,lng,city):
    account = jodel_api.JodelAccount(lat=lat, lng=lng, city=city)
    while True:
        try:
            a = jodel_api.AndroidAccount()
            account.verify(a)
            account.get_account_data()
            break
        except:
            raise Exception("Couldn't verify account. Please retry in a few Minutes.")
    return InputJodelAcc(access_token=account.access_token,expiration_date=account.expiration_date,refresh_token=account.refresh_token,distinct_id=account.distinct_id,device_uid=account.device_uid, legacy=False)

def get_Jodels_loc():
    print("Input the location your Jodels should be posted at:\n")
    lat = input("Latitude:\n")
    lng = input("Longitude:\n")
    city = input("City:\n")
    return InputJodelAcc(lat=lat,lng=lng,city=city)

def get_data_Weather():
    while True:
        print("Input the data for the Wunderground weather API.\n")
        API_KEY = input("API Key:\n")
        COUNTRY = input("Country:\n")
        CITY = input("City:\n")
        CITY_code = check_weather(API_KEY,COUNTRY, CITY)
        if CITY_code == False:
            if y_n("Retry?") == False:
                raise Exception("User abort on Weather Data select.")
        else:
            break
    while True:
        print("Input the data for the DWD FTP Server.\n")
        dwdname = input("Username:\n")
        dwdpass = input("Password:\n")
        if not check_dwdftp(dwdname, dwdpass):        
            if y_n("Retry?") == False:
                raise Exception("User abort on DWD FTP Server data input.")
        else:
            break             
    return InputWeather(API_KEY, CITY_code,dwdname,dwdpass)

def check_weather(API_KEY, COUNTRY, CITY):
    response = requests.get("https://api.wunderground.com/api/%s/geolookup/q/%s/%s.json" % (API_KEY,COUNTRY,CITY))
    response_json = response.json()
    if "location" in response_json:
        CITY_code = response_json["location"]["l"]
        CITY_code = CITY_code[7:]
        return CITY_code
    
    if "error" in response_json["response"]:
        if response_json["response"]["error"]["type"] == "keynotfound":
            print("Invalid API Key!")
            return False
        elif response_json["response"]["error"]["type"] == "querynotfound":
            print("City not found!")
            return False

    results_sorted = sorted(response_json["response"]["results"], key=itemgetter('country_name')) 
    if "results" in response_json["response"]:
        results_num = 0
        for item in results_sorted:
            print("{0}. {1}, {2}, {3}".format(results_num,item["name"], item["state"],item["country_name"]))
            results_num = results_num + 1
        CITY_code = (results_sorted[int(input("Choose a city by typing it's number:\n"))])["zmw"]
        return CITY_code
      
    raise Exception("Got invalid data from Weather Provider.\nData:%s" % response_json)

def check_dwdftp(dwdname, dwdpass):
    try:
        ftp = FTP('ftp-outgoing2.dwd.de')
        ftp.login(dwdname, dwdpass)
        return True
    except:
        print("Invalid username or password")
        return False


filename = input("Choose an account file name:\n")
write_data(create_data(),filename)
print('Data has been successfully written. You can now use "jodel_wetterfrosch.py"')
