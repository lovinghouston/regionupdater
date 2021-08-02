from geopandas.io.file import read_file
from numpy import cumproduct
from shapely.geometry import Polygon, Point
import shapely.speedups
shapely.speedups.enable()
from pyproj import Transformer
import geopandas as gpd
import csv

HoustonISD = gpd.read_file("Original/HighAttendanceZones1920.shp")

lati,long = 29.693211, -95.272556 #29.737586775000725, -95.40166115040519 #29.735600, -95.328620
CurPoint = Point(Transformer.from_crs("epsg:4326", "epsg:2278").transform(lati,long))

churches = []
with open("20210727_Loving-Houston-Church-Account-Longitude-and-Latitude-Sheet1.csv") as csvfile:
    reader = csv.reader(csvfile)
    for row in reader: # each row is a list
        churches.append(row)
for idx,val in enumerate(churches[0]):
    if val == "Name":
        NameIndex = idx
    if val == "BillingLongitude":
        LongIndex = idx
    if val == "BillingLatitude":
        LatIndex = idx
numfields = len(churches[0])

print(HoustonISD.loc[0][1])
print(churches[1])
print(CurPoint)