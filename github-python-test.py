from geopandas.io.file import read_file
from numpy import cumproduct
from shapely.geometry import Polygon, Point
import shapely.speedups
shapely.speedups.enable()
from pyproj import Transformer
import geopandas as gpd
import csv

# HoustonISD = gpd.read_file("C:/Users/crazy/OneDrive/Documents/VS Code Stuff/HighAttendanceZones1920/Original/HighAttendanceZones1920.shp")

lati,long = 29.693211, -95.272556 #29.737586775000725, -95.40166115040519 #29.735600, -95.328620
CurPoint = Point(Transformer.from_crs("epsg:4326", "epsg:2278").transform(lati,long))

# print(HoustonISD.loc[0][1])
print(CurPoint)