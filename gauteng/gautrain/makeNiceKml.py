#!/usr/bin/python -ttO
# -*- coding: utf-8 -*-

# Requires simplekml. Install with easy_install

import simplekml
import transitfeed

default_color = 'ffffff'


#TODO: Add icons based on trip type

kml = simplekml.Kml()
gtfs = transitfeed.Schedule()
gtfs.Load("gautrain_unofficial.zip")

kmlroutes = kml.newfolder(name="Routes")

# TODO: Split by type
for route in gtfs.GetRouteList():
  routefolder = kmlroutes.newfolder(name=route["route_short_name"])
  pid_trips = route.GetPatternIdTripDict()
  for pattern_id in pid_trips.keys():
    trip = pid_trips[pattern_id][0] # Since we only want to map, any trip will do
    print trip["trip_id"],route["route_id"]
    if trip["direction_id"] == "1":
      direction = " (Reverse)"
    else:
 #     direction = " (Forward)"
      direction = ""
    shape = gtfs.GetShape(trip["shape_id"])
    coords = [(lon, lat) for (lat, lon, dist) in shape.points]
    name = route["route_short_name"]+": "+route["route_long_name"]+direction
    line = routefolder.newlinestring(name=name,coords=coords)
    line.iconstyle = simplekml.IconStyle(icon=simplekml.Icon(href="http://maps.google.com/mapfiles/kml/pal2/icon13.png"))
    if "route_color" in route.keys() and route.route_color != '':
      color = "8F"+route.route_color
    else:
      color = "8F"+default_color
    line.linestyle = simplekml.LineStyle(width=4,color=color)
    stopfolder = routefolder.newfolder(name="Stops")
    for stop in trip.GetPattern():
        coords=[( stop.stop_lon, stop.stop_lat )]
        stopfolder.newpoint(coords=coords,name=stop.stop_name)
# TODO: Stops not in any route
#orphan_stops = kml.newfolder(name="Unused Stops")
# Possible TODO: handle multiple instances of same stop

kml.save("test.kml",False)
