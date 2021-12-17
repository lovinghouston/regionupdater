from geopandas.io.file import read_file
from numpy import cumproduct
from shapely.geometry import Polygon, Point #install
import shapely.speedups
shapely.speedups.enable()
from pyproj import Transformer
import geopandas as gpd #install
import json
import csv
import requests #install
import os

#figure out what happened with that Kansas one

HoustonISD = gpd.read_file("shape/HoustonISD/HighAttendanceZones1920.shp")
TexasDistricts = gpd.read_file("shape/TexasSchoolDistricts/SchoolDistricts_2021.shp")

iterationsEnd = int(os.environ.get('ITERATIONS_END'))
alldistricts = [] #TEMPORARY
#ITERATIONS_END = 2000 #For testing - ends iterations early
churches = []
logResults = []
logResults.append(["Number","Church Account ID","Church Name","Region Update Input","API Response Text","Error"])

#Retrieve Access Token
#Uses REST password grant type i.e: https://developer.salesforce.com/docs/atlas.en-us.api_iot.meta/api_iot/qs_auth_access_token.htm
url = os.environ.get('PROD_AUTH_URL') #put information to get token
payload = ""
headers = {
  'Cookie': 'BrowserId=L1U6KxlzEeuszK_80mI4gA; CookieConsentPolicy=0:0'
}
response = requests.request("POST", url, headers=headers, data=payload)
tokenTemp = response.text.replace('"',"").split(',')
ttype = tokenTemp[3].split(':')[1]
token = "" + ttype + " " + tokenTemp[0].split(':')[1] + ""

#url query to get Church data
#Note: Changed date to 7200 for testing purposes
url = "https://lovinghouston.my.salesforce.com/services/data/v40.0/query/?q=SELECT+Id,Name,BillingLongitude,BillingLatitude,Parent.Name,Houston_ISD_Region__c+FROM+Account+WHERE+(Type+=+'Church'+AND+BillingLongitude+!=+null+AND+Houston_ISD_Region__c+=+null+AND+CreatedDate+=+LAST_N_DAYS:7200)+OR+(Type+=+'Church'+AND+BillingLongitude+!=+null+AND+Parent.Name+=+'Houston+ISD'+AND+Houston_ISD_Region__c+=+null+AND+CreatedDate+=+LAST_N_DAYS:7200)+ORDER+BY+LastModifiedDate+DESC"
headers = {
    'Authorization': token
}
response = requests.request("GET", url, headers=headers)
reader = json.loads(response.text)


#Check if token is expired and quit program if so
if response.text == '[{"message":"Session expired or invalid","errorCode":"INVALID_SESSION_ID"}]':
    print(response.text)
    exit()

print(reader)

#Read churches query into churches list, define indices and format
for i in range(len(reader["records"])):
    tempID = reader["records"][i]["Id"]
    templong = reader["records"][i]["BillingLongitude"]
    templat = reader["records"][i]["BillingLatitude"]
    tempname = reader["records"][i]["Name"]
    row = tempID, tempname, templong, templat
    IDIndex, NameIndex, LongIndex, LatIndex = 0,1,2,3
    churches.append(row)

#Switch function to parse area numbers into Houston ISD regions
def RegionSwitch(argument):
    switcher = {
    0: "East",
    1: "West",
    2: "East",
    3: "North",
    4: "East",
    5: "North",
    6: "North",
    7: "Northwest",
    8: "West",
    9: "South",
    10: "East",
    11: "North",
    12: "Northwest",
    13: "Northwest",
    14: "West",
    15: "South",
    16: "Northwest",
    17: "North",
    18: "South",
    19: "West",
    20: "North",
    21: "South",
    22: "East",
    }
    return switcher.get(argument, "Not in Houston ISD polygons")

#Switch function to parse district names into Salesforce Account IDs
def DistrictSwitch(argument): #NOT DONE
    switcher = {
    'Spring ISD': "0011N000018j7K1QAI",
    'New Caney ISD': "0011N000018j7K2QAI",
    'Alief ISD': "0011N000018j7K3QAI",
    'Clear Creek ISD': "0011N000018j7K4QAI",
    'Conroe ISD': "0011N000018j7K5QAI",
    'Cypress-Fairbanks ISD': "0011N000018j7K6QAI",
    'Katy ISD': "0011N000018j7K8QAI",
    'Pasadena ISD': "0011N000018j7K9QAI",
    'Waller ISD': "0011N000018j7KAQAY",
    'Yes Prep': "0011N000018j7KBQAY",
    'Tomball ISD': "0011N000018j7KCQAY",
    'Humble ISD': "0011N000018j7KEQAY",
    'North Forest ISD': "0011N000018j7KFQAY",
    'La Porte ISD': "0011N000018j7KGQAY",
    'Pearland ISD': "0011N000018j7KHQAY",
    'Crosby ISD': "0011N000018j7KIQAY",
    'East Chambers ISD': "0011N000018j7KJQAY",
    'Galena Park ISD': "0011N000018j7KKQAY",
    'Kipp': "0011N000018j7KMQAY",
    'Aldine ISD': "0011N000018j7KNQAY",
    'Channelview ISD': "0011N000018j7KOQAY",
    'Goose Creek CISD': "0011N000018j7JrQAI",
    'James Deanda Elementary': "0013l00002OL0SPAA1",
    'Brenham ISD': "0013l00002RLyxLAAT",
    'Southwest Schools': "0013l00002RL9gUAAT",
    'Milne Elementary School': "0013l00002OnploAAB",
    'Spring Branch ISD': "0011N000018iy7eQAA",
    'Klein ISD': "0011N000018iyCRQAY",
    'Lamar Cons ISD': "0011N000018iyBMQAY",
    'Sheldon ISD': "0013l00002Hm1BrAAJ",
    'Houston ISD': "0011N000018iyKTQAY",
    'Fort Bend ISD': "0011N000018iyQhQAI",
    'Angleton ISD': "0011N00001VYEEsQAP",
    'Brazosport ISD': "0011N00001VYDr2QAH",
    'Bryan ISD': "0011N00001jzfldQAA",
    'Windham School District': "0011N00001k0DqsQAE",
    'Port Neches-Groves ISD': "0011N00001k0fYmQAI",
    'Alamo Heights ISD': "0011N00001k0fXkQAI",
    }
    return switcher.get(argument, "")

#Function to compare point against Houston ISD areas polygons
def Locate(church,point):
    region = ""
    for reg in range(len(HoustonISD)):
        if point.within(HoustonISD.loc[reg, 'geometry']) == 1:
            region = '{"Houston_ISD_Region__c": "' + RegionSwitch(reg) + '", "School_District_Lookup__c": "0011N000018iyKTQAY"}'
    return region

#Function to compare point against Texas School Districts polygons
def DistLocate(church,point):
    district = ""
    for dist in range(len(TexasDistricts)):
        if point.within(TexasDistricts.loc[dist]['geometry']) == 1:
            district = '{"Houston_ISD_Region__c": "N/A", "School_District_Lookup__c": "' + DistrictSwitch(TexasDistricts.loc[dist]['NAME']) + '"}'
#            alldistricts.append(TexasDistricts.loc[dist]['NAME'])
    return district

#Iterate through each church, transforms lat/long from Google Maps map system into Houston ISD or Texas Districts system
#Then, uploads result to Salesforce
for i in range(len(churches)):
    anyError = ""
    CurChurch = churches[i][NameIndex]
    if churches[i][LongIndex] == '' or churches[i][LatIndex] == '':
        continue
    CurPoint = Point(Transformer.from_crs("epsg:4326", "epsg:2278").transform(churches[i][LatIndex],churches[i][LongIndex]))
    result = Locate(CurChurch,CurPoint)
    if result == "":
        CurPoint = Point(Transformer.from_crs("epsg:4326", "epsg:3081").transform(churches[i][LatIndex],churches[i][LongIndex]))
        result = DistLocate(CurChurch,CurPoint)

    print(str(i) + " " + str(churches[i][IDIndex]) + ": " + str(result) + " " + str(CurChurch))

    url = "https://lovinghouston.my.salesforce.com/services/data/v50.0/sobjects/Account/" + str(churches[i][IDIndex])
    headers = {
        'Content-Type': 'application/json',
        'Authorization': token
    }
    response = requests.request("PATCH", url, headers=headers, data=result)
#    print(response.text)

#Collect data (number, Account ID, Church Name, Data sent to Salesforce, response from API, Errors input here) into a line to log
    logLine = [i,churches[i][IDIndex],CurChurch,result,response.text,anyError]
    logResults.append(logLine)

#Temporary testing tool to cull number iterations early
    if i>iterationsEnd:
        break

#Enter logged data into CSV
with open('RegionUpdaterResultsTracker.csv', 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerows(logResults)

#   Along with alldistricts definition above in DistLocate function, this provides list of all identified districts where churches are located
#alldistricts = list(set(alldistricts))
#print(alldistricts)
 
