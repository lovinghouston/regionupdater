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

#get terminal text if it fails
#return that as error in the tracker (change the name of the CSV too)
#figure out what happened with that Kansas one

HoustonISD = gpd.read_file("shape/HoustonISD/HighAttendanceZones1920.shp")
TexasDistricts = gpd.read_file("shape/TexasSchoolDistricts/SchoolDistricts_2021.shp")

alldistricts = [] #TEMPORARY
churches = []
logResults = []
logResults.append(["Number","Church Account ID","Church Name","Region Update Input","API Response Text","Error"])

#url query to get Church data
#Note: Changed date to 7200 for testing purposes
url = "https://lovinghouston--partial.my.salesforce.com/services/data/v40.0/query/?q=SELECT+Id,Name,BillingLongitude,BillingLatitude+FROM+Account+WHERE+Type+=+'Church'+AND+BillingLongitude+!=+null+AND+Houston_ISD_Region__c+=+null+AND+CreatedDate+=+LAST_N_DAYS:7200"
headers = {
    'Authorization': 'Bearer {{SF_ACCESS_TOKEN}}'
}
response = requests.request("GET", url, headers=headers)
reader = json.loads(response.text)

#with open("./Json query test.json", "w+") as jsonfile:
#    jsonfile.write(response.text)
#    reader = json.load(jsonfile)

#Read church JSON
for i in range(len(reader["records"])):
    tempID = reader["records"][i]["Id"]
    templong = reader["records"][i]["BillingLongitude"]
    templat = reader["records"][i]["BillingLatitude"]
    tempname = reader["records"][i]["Name"]
    row = tempID, tempname, templong, templat
    IDIndex, NameIndex, LongIndex, LatIndex = 0,1,2,3
    churches.append(row)

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

def DistrictSwitch(argument): #NOT DONE
    switcher = {
#    'Columbus ISD': "",
    'Cypress-Fairbanks ISD': "0011N000018j7K6QAI",
#    'Spring Branch ISD': "0011N000018iy7eQAA",
    'Aldine ISD': "0011N000018j7KNQAY",
    'Tomball ISD': "0011N000018j7KCQAY",
    'Pasadena ISD': "0011N000018j7K9QAI",
#    'Dickinson ISD': "",
    'New Caney ISD': "0011N000018j7K2QAI",
    'Sheldon ISD': "0013l00002Hm1BrAAJ",
#    'Lamar Cons ISD': "0011N000018iyBMQAY",
    'Katy ISD': "0011N000018j7K8QAI",
    'Spring ISD': "0011N000018j7K1QAI",
    'Galena Park ISD': "0011N000018j7KKQAY",
    'Conroe ISD': "0011N000018j7K5QAI",
    'Brazosport ISD': "0011N00001VYDr2QAH",
    'Humble ISD': "0011N000018j7KEQAY",
    'Pearland ISD': "0011N000018j7KHQAY",
#    'Beaumont ISD': "",
#    'Fort Bend ISD': "0011N000018iyQhQAI",
    'Clear Creek ISD': "0011N000018j7K4QAI",
#    'Klein ISD': "0011N000018iyCRQAY",
    'Alief ISD': "0011N000018j7K3QAI",
#    'Stafford MSD': "",
    }
    return switcher.get(argument, "")

def Locate(church,point):
    region = ""
    for reg in range(len(HoustonISD)):
        if point.within(HoustonISD.loc[reg, 'geometry']) == 1:
            region = '{"Houston_ISD_Region__c": "' + RegionSwitch(reg) + '", "ParentID": "0016t00000AmYsRAAV"}'
    return region

def DistLocate(church,point):
    district = ""
    for dist in range(len(TexasDistricts)):
        if point.within(TexasDistricts.loc[dist]['geometry']) == 1:
            district = '{"Houston_ISD_Region__c": "N/A", "ParentId": "' + DistrictSwitch(TexasDistricts.loc[dist]['NAME']) + '"}'
#            alldistricts.append(TexasDistricts.loc[dist]['NAME'])
    return district

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

    url = "https://lovinghouston--partial.my.salesforce.com/services/data/v50.0/sobjects/Account/" + str(churches[i][IDIndex])
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer 00D6t0000008fyq!AR0AQOt8H7EF0pMj3A3Z9uOP9xGtYR4Q10LLaM5xdG6vsrr3Y4wX5n321xB0KiQo40.t9ooja9EjdVyG7y2VA9HuGEj3Y1iw'
    }
    response = requests.request("PATCH", url, headers=headers, data=result)

#    print(response.text)

    logLine = [i,churches[i][IDIndex],CurChurch,result,response.text,anyError]
    logResults.append(logLine)

    if i<20:
        break

with open('Region Updater Results Tracker.csv', 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile) 
    csvwriter.writerows(logResults)


#alldistricts = list(set(alldistricts))
#print(alldistricts)
