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
