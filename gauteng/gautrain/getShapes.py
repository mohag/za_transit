#!/usr/bin/python -ttO

# Imports shapes, dump in python format

import pprint
import sys
import xml.dom.minidom as minidom
import xml.etree.ElementTree as etree

shapes = {}

tree = etree.ElementTree()
tree.parse(sys.argv[1])
for place in tree.findall(".//{http://www.opengis.net/kml/2.2}Placemark"):
  name = place.findtext(".//{http://www.opengis.net/kml/2.2}name")
  shapes[name] = []
  for line in place.findall(".//{http://www.opengis.net/kml/2.2}LineString"):
    for coords in place.findall(".//{http://www.opengis.net/kml/2.2}coordinates"):
      for coord in coords.text.rstrip().lstrip().split(" "):
        tmp = []
        lon,lat,tmp = coord.split(",")
        shapes[name].append([lat,lon])
pp = pprint.PrettyPrinter(indent=2)
print "hardcoded_shapes = ",pp.pformat(shapes)
