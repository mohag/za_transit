#!/usr/bin/python -ttO
# -*- coding: utf-8 -*-
# This is my first Python script that does some actual work... Expect ugliness...
# Tested under Python 2.7 on Linux
#
# getRoutes.py - a script to build basic GTFS data for the Gautrain
#    Copyright (C) 2011 Gert van den Berg
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program in the file CODE-LICENSE.
#    If not, see <http://www.gnu.org/licenses/agpl.html>.
#

# Imports
import sys
import re
import array
import math

try: import httplib
except ImportError: import http.client as httplib

try: import simplejson as json
except ImportError: import json

try: import transitfeed
except ImportError:
  print "Can't find transitfeed. Ensure that transitfeed is installed"
  sys.exit(1)

############################ Configuration ###################################
debug = 1

#### TODO: Agency
# Agency definitions
agencies = {
  'za_gautrain':{
    'agency_name':'Gautrain Management Agency',
    'agency_timezone':'Africa/Johannesburg',
    'agency_phone':'0800 GAUTRAIN',
    'agency_fare_url':'http://www.gautraincard.co.za/',
    'agency_url':'http://www.gautrain.co.za/',
    'agency_acronym':'GMA',
    'agency_lang':'en',
  },
}
### End of agency config

##### Calender
cal_start = '20110802' # From when is this valid
cal_end   = '20121231' # Until when is this valid
cal_no_service = [] # Array of days without anyi weekend/weekday service - special service can overwrite
cal_holiday = [ # Array of days with weekend service rather than weekday service
    # 2011
    "20110809", "20110924", "20111216", "20111225", "20111226",
    # 2012
    "20120101","20120102","20120321","20120406","20120409","20120427","20120501","20120616",
    "20120809","20120924","20121216","20121217","20121225","20121226" 
  ] 
cal_extra_weekday = [] # Array of days with weekday service (Rather than default (probably weekend if listed here))
cal_special_service = [ # Array of maps of special service. Is added to normal, use no service to delete normal service
# Format template:
#  {
#    "date":"20991231",
#    "service_id":""
#  },
]
##### End of calender configuration

##### Routes
# Descriptions for routes
route_describe = {
 # Train routes
 'gautrain_ns' : 'North-South Gautrain route. Runs between Hatfield Station and Park Station',
 'gautrain_ew' : 'East-West route running between OR Tambo Station and Sandton Station',
 # Bus routes
 'H1' : 'Runs from Hatfield Station to Nieuw Muckleneuk and Waterkloof',
 'H2' : 'Runs from Hatfield Station to Lynnwood Manor',
 'H3' : 'Runs from Hatfield Station to Arcadia',
 'H4' : 'Runs from Hatfield Station to Waverley',
 'H5' : 'Runs from Hatfield Station to Menlyn',
 'P1' : 'Runs from Pretoria Station through CBD with Visagie, Streuben and Prinsloo Street',
 'P2' : 'Runs from Pretoria Station through CBD with Bosman and Andries Street',
 'C1' : 'Runs from Centurion station to Techno Park and Eco Park Estate',
 'C2' : 'Runs from Centurion station to Rooihuiskraal and Amberfield',
 'C3' : 'Runs from Centurion station to Wierda Park',
 'C4' : 'Runs from Centurion station through Doringkloof to Southdowns',
 'M1' : 'Runs from Midrand station through Randjespark',
 'M2' : 'Runs from Midrand station to Noordwyk past Vodaworld and Midridge Park',
 'M3' : 'Runs from Midrand station to Sunninghill through Halfway House',
 'S2' : 'Runs from Sandton station to Gallo Manor though Wendywood',
 'S3' : 'Runs from Sandton station to Rivonia through Morningside',
 'S4' : 'Runs from Sandton station through Randburg',
 'S5' : 'Runs from Sandton station to Fourways through Bryanston',
 'RB1' : 'Runs from Rosbank Station to Highlands North',
 'RB2' : 'Runs from Rosebank Station to Melrose Arch',
 'RB3' : 'Runs from Rosebank Station to Illovo',
 'RB4' : 'Runs from Rosebank Station to Hyde Park',
 'RB5' : 'Temporary bus from Rosebank to Park Station',
 'RF1' : 'Runs from Rhodesfield station through Kempton Park to Aston Manor',
 'J1' : 'Runs From Park Station to Parktown',
}
# Per route route_url values... Too long for override list
route_link = {
 'gautrain_ns': '',
 'gautrain_ew': '',
}
default_route = {
  "route_id"             :"",
  "agency_id"            :"za_gautrain",
  "route_short_name"     :"",
  "route_long_name"      :"",
  "route_desc"           :"",
  "route_type"           :"",
  "route_url"            :"",
  "route_color"          :"",
  "route_text_color"     :"FFFFFF",
  "generic_service_name" :"Gautrain Bus"
}
# Routes to delete - usually to replace with manual overwritten one - array of route_id
route_delete = []
# Manual override for incorrect values fed from site
route_overwrite = {
}
# Hardcoded routes - routes with blank route_id gets ignored
hardcoded_routes = [
  {
    "route_id"             :"gautrain_ns",
    "agency_id"            :"za_gautrain",
    "route_short_name"     :"N-S",
    "route_long_name"      :"North-South line",
    "route_desc"           :route_describe["gautrain_ns"],
    "route_type"           :"2",
    "route_url"            :route_link["gautrain_ns"],
    "route_color"          :"",
    "route_text_color"     :"",
    "generic_service_name" :"Gautrain"
  },
  {
    "route_id"             :"gautrain_ew",
    "agency_id"            :"za_gautrain",
    "route_short_name"     :"E-W",
    "route_long_name"      :"East-West line",
    "route_desc"           :route_describe["gautrain_ew"], 
    "route_type"           :"2",
    "route_url"            :route_link["gautrain_ew"],
    "route_color"          :"",
    "route_text_color"     :"",
    "generic_service_name" :"Gautrain"
  },
  { # Template - ignored because of blank route_id
    "route_id"             :"",
    "agency_id"            :"za_gautrain",
    "route_short_name"     :"",
    "route_long_name"      :"",
    "route_desc"           :"", # see route_describe
    "route_type"           :"", # 1 - Tram, 2 - Subway/Metro, 3 - Bus
    "route_url"            :"", # see route_link
#    "route_url"            :route_link[""],
    "route_color"          :"",
    "route_text_color"     :"",
    "generic_service_name" :"Gautrain"
  },
]
#### End of route config

##### Stops
# Stop URLs - too long for override list
stop_link = {
 'hatfield_station'    : 'http://www.gautrain.co.za/about/route/stations/hatfield-station/',
 'pretoria_station'    : 'http://www.gautrain.co.za/about/route/stations/background-to-pretoria-station/',
 'centurion_station'   : 'http://www.gautrain.co.za/about/route/stations/centurion-station/',
 'midrand_station'     : 'http://www.gautrain.co.za/about/route/stations/background-to-midrand-station/',
 'marlboro_station'    : 'http://www.gautrain.co.za/about/route/stations/marlboro-station/',
 'sandton_station'     : 'http://www.gautrain.co.za/about/route/stations/sandton-station/',
 'rosebank_station'    : 'http://www.gautrain.co.za/about/route/stations/rosebank-station-gps/',
 'park_station'        : 'http://www.gautrain.co.za/about/route/stations/gautrains-johannesburg-park-station/',
 'rhodesfield_station' : 'http://www.gautrain.co.za/about/route/stations/rhodesfield-station/',
 'ortambo_station'     : 'http://www.gautrain.co.za/about/route/stations/or-tambo-international-airport-station/',
}
# Stop Descrition - too long for override list
stop_describe = {
}
# Stops to delete - array of stop_id
stop_delete = []
# stop parameter override list
stop_overwrite = {
 'o_r__tambo_station' : {"order":0,"stop_id":'ortambo_station'}, # Need to be processed first
 'M1_0'               : {"order":0,"stop_id":"hatfield_bus","stop_code":"","stop_name":"Midrand Station Bus Stop","parent_station":"hatfield_station"},
 'Rb1_0'              : {"order":0,"stop_id":"rosebank_bus","stop_code":"","stop_name":"Rosebank Station Bus Stop","parent_station":"rosebank_station"},
 'C1_0'               : {"order":0,"stop_id":"centurion_bus","stop_code":"","stop_name":"Centurion Station Bus Stop","parent_station":"centurion_station"},
 'H1_0'               : {"order":0,"stop_id":"hatfield_bus","stop_code":"","stop_name":"Hatfield Station Bus Stop","parent_station":"hatfield_station"},
 'P1_0'               : {"order":0,"stop_id":"pretoria_bus","stop_code":"","stop_name":"Pretoria Station Bus Stop","parent_station":"pretoria_station"},
 'RB5_0'              : {"order":0,"stop_id":"J1_0"},
# 'J1_0'               : {"order":10,"stop_id":"park_bus","stop_code":"","stop_name":"Park Station Bus Stop","parent_station":"park_station"},
 'hatfield_station'   : {"order":0,"location_type":"1"},
 'pretoria_station'   : {"order":0,"location_type":"1"},
 'centurion_station'  : {"order":0,"location_type":"1"},
 'midrand_station'    : {"order":0,"location_type":"1"},
 'marlboro_station'   : {"order":0,"location_type":"1"},
 'sandton_station'    : {"order":0,"location_type":"1"},
 'rosebank_station'   : {"order":0,"location_type":"1"},
 'park_station'       : {"order":0,"location_type":"1"},
 'rhodesfield_station': {"order":0,"location_type":"1"},
 'Rb1_6'              : {"order":0,"stop_lat":'-26.1446333333333'}, # incorrect on site
 'H5_21'              : {"order":0,"stop_lat":'-25.7547666666667','stop_lon':'28.2398833333333'}, # incorrect on site
 'C1_1'               : {"order":0,"stop_lat":'-25.8587333333333','stop_lon':'28.1966666666667'}, # data on site is broken
 'ortambo_station'    : {"order":10,"location_type":"1","stop_name":"O.R. Tambo Airport Station"},
}
# Values to be used if none other given
default_stop = {
   "stop_id":"",
   "stop_code":"",
   "stop_name":"Unnamed stop",
   "stop_desc":"",
   "stop_lat":"",
   "stop_lon":"",
   "zone_id":"",
   "stop_url":"",
   "location_type":"0",
   "parent_station":"",
   "wheelchair_boarding":"1", # Gautrain system is wheelchair accessible
   "stop_timezone":""
 }
# values for hardcoded stops - not created from lists - no overrides apply here - you can just change the declaration
# Data not on site - Platforms, Bus terminals
hardcoded_stops = [
 {
   "stop_id":"hatfield_platform_ns",
   "stop_code":"",
   "stop_name":"Hatfield Platform ",
   "stop_desc":"",
   "stop_lat":-25.74765,
   "stop_lon":28.238,
   "zone_id":"",
   "stop_url":"",
   "location_type":"0",
   "parent_station":"hatfield_station",
   "wheelchair_boarding":"1",
   "stop_timezone":""
 },
 {
   "stop_id":"hatfield_platform_sn",
   "stop_code":"",
   "stop_name":"Hatfield Platform ",
   "stop_desc":"",
   "stop_lat":-25.74765,
   "stop_lon":28.238,
   "zone_id":"",
   "stop_url":"",
   "location_type":"0",
   "parent_station":"hatfield_station",
   "wheelchair_boarding":"1",
   "stop_timezone":""
 },
 {
   "stop_id":"pretoria_platform_ns",
   "stop_code":"",
   "stop_name":"Pretoria Platform ",
   "stop_desc":"",
   "stop_lat":-25.758167,
   "stop_lon":28.189467,
   "zone_id":"",
   "stop_url":"",
   "location_type":"0",
   "parent_station":"pretoria_station",
   "wheelchair_boarding":"1",
   "stop_timezone":""
 },
 {
   "stop_id":"pretoria_platform_sn",
   "stop_code":"",
   "stop_name":"Pretoria Platform ",
   "stop_desc":"",
   "stop_lat":-25.758167,
   "stop_lon":28.189467,
   "zone_id":"",
   "stop_url":"",
   "location_type":"0",
   "parent_station":"pretoria_station",
   "wheelchair_boarding":"1",
   "stop_timezone":""
 },
 {
   "stop_id":"centurion_platform_ns",
   "stop_code":"",
   "stop_name":"Centurion Platform B",
   "stop_desc":"",
   "stop_lat":-25.85162,
   "stop_lon":28.189733,
   "zone_id":"",
   "stop_url":"",
   "location_type":"0",
   "parent_station":"centurion_station",
   "wheelchair_boarding":"1",
   "stop_timezone":""
 },
 {
   "stop_id":"centurion_platform_sn",
   "stop_code":"",
   "stop_name":"Centurion Platform A",
   "stop_desc":"",
   "stop_lat":-25.85162,
   "stop_lon":28.189733,
   "zone_id":"",
   "stop_url":"",
   "location_type":"0",
   "parent_station":"centurion_station",
   "wheelchair_boarding":"1",
   "stop_timezone":""
 },
 {
   "stop_id":"midrand_platform_ns",
   "stop_code":"",
   "stop_name":"Midrand Platform ",
   "stop_desc":"",
   "stop_lat":-25.99648,
   "stop_lon":28.137583,
   "zone_id":"",
   "stop_url":"",
   "location_type":"0",
   "parent_station":"midrand_station",
   "wheelchair_boarding":"1",
   "stop_timezone":""
 },
 {
   "stop_id":"midrand_platform_sn",
   "stop_code":"",
   "stop_name":"Midrand Platform ",
   "stop_desc":"",
   "stop_lat":-25.99648,
   "stop_lon":28.137583,
   "zone_id":"",
   "stop_url":"",
   "location_type":"0",
   "parent_station":"midrand_station",
   "wheelchair_boarding":"1",
   "stop_timezone":""
 },
 {
   "stop_id":"marlboro_platform_ew",
   "stop_code":"",
   "stop_name":"Marlboro Platform D",
   "stop_desc":"",
   "stop_lat":-26.083917,
   "stop_lon":28.111633,
   "zone_id":"",
   "stop_url":"",
   "location_type":"0",
   "parent_station":"marlboro_station",
   "wheelchair_boarding":"1",
   "stop_timezone":""
 },
 {
   "stop_id":"marlboro_platform_we",
   "stop_code":"",
   "stop_name":"Marlboro Platform C",
   "stop_desc":"",
   "stop_lat":-26.083917,
   "stop_lon":28.111633,
   "zone_id":"",
   "stop_url":"",
   "location_type":"0",
   "parent_station":"marlboro_station",
   "wheelchair_boarding":"1",
   "stop_timezone":""
 },
 {
   "stop_id":"marlboro_platform_ns",
   "stop_code":"",
   "stop_name":"Marlboro Platform B",
   "stop_desc":"",
   "stop_lat":-26.083917,
   "stop_lon":28.111633,
   "zone_id":"",
   "stop_url":"",
   "location_type":"0",
   "parent_station":"marlboro_station",
   "wheelchair_boarding":"1",
   "stop_timezone":""
 },
 {
   "stop_id":"marlboro_platform_sn",
   "stop_code":"",
   "stop_name":"Marlboro Platform A",
   "stop_desc":"",
   "stop_lat":-26.083917,
   "stop_lon":28.111633,
   "zone_id":"",
   "stop_url":"",
   "location_type":"0",
   "parent_station":"marlboro_station",
   "wheelchair_boarding":"1",
   "stop_timezone":""
 },
 {
   "stop_id":"sandton_platform_ns",
   "stop_code":"",
   "stop_name":"Sandton Platform ",
   "stop_desc":"",
   "stop_lat":-26.1078,
   "stop_lon":28.0575,
   "zone_id":"",
   "stop_url":"",
   "location_type":"0",
   "parent_station":"sandton_station",
   "wheelchair_boarding":"1",
   "stop_timezone":""
 },
 {
   "stop_id":"sandton_platform_sn",
   "stop_code":"",
   "stop_name":"Sandton Platform ",
   "stop_desc":"",
   "stop_lat":-26.1078,
   "stop_lon":28.0575,
   "zone_id":"",
   "stop_url":"",
   "location_type":"0",
   "parent_station":"sandton_station",
   "wheelchair_boarding":"1",
   "stop_timezone":""
 },
 {
   "stop_id":"sandton_platform_ew",
   "stop_code":"",
   "stop_name":"Sandton Platform ",
   "stop_desc":"",
   "stop_lat":-26.1078,
   "stop_lon":28.0575,
   "zone_id":"",
   "stop_url":"",
   "location_type":"0",
   "parent_station":"sandton_station",
   "wheelchair_boarding":"1",
   "stop_timezone":""
 },
 {
   "stop_id":"sandton_platform_we",
   "stop_code":"",
   "stop_name":"Sandton Platform ",
   "stop_desc":"",
   "stop_lat":-26.1078,
   "stop_lon":28.0575,
   "zone_id":"",
   "stop_url":"",
   "location_type":"0",
   "parent_station":"sandton_station",
   "wheelchair_boarding":"1",
   "stop_timezone":""
 },
 {
   "stop_id":"rosebank_platform_ns",
   "stop_code":"",
   "stop_name":"Rosebank Platform ",
   "stop_desc":"",
   "stop_lat":-26.14525,
   "stop_lon":28.0438667,
   "zone_id":"",
   "stop_url":"",
   "location_type":"0",
   "parent_station":"rosebank_station",
   "wheelchair_boarding":"1",
   "stop_timezone":""
 },
 {
   "stop_id":"rosebank_platform_sn",
   "stop_code":"",
   "stop_name":"Rosebank Platform ",
   "stop_desc":"",
   "stop_lat":-26.14525,
   "stop_lon":28.0438667,
   "zone_id":"",
   "stop_url":"",
   "location_type":"0",
   "parent_station":"rosebank_station",
   "wheelchair_boarding":"1",
   "stop_timezone":""
 },
 {
   "stop_id":"park_platform_ns",
   "stop_code":"",
   "stop_name":"Park Station Platform ",
   "stop_desc":"",
   "stop_lat":-26.195533,
   "stop_lon":28.04155,
   "zone_id":"",
   "stop_url":"",
   "location_type":"0",
   "parent_station":"park_station",
   "wheelchair_boarding":"1",
   "stop_timezone":""
 },
 {
   "stop_id":"park_platform_sn",
   "stop_code":"",
   "stop_name":"Park Station Platform ",
   "stop_desc":"",
   "stop_lat":-26.195533,
   "stop_lon":28.04155,
   "zone_id":"",
   "stop_url":"",
   "location_type":"0",
   "parent_station":"park_station",
   "wheelchair_boarding":"1",
   "stop_timezone":""
 },
 {
   "stop_id":"rhodesfield_platform_ew",
   "stop_code":"",
   "stop_name":"Rhodesfield Platform ",
   "stop_desc":"",
   "stop_lat":-26.128333,
   "stop_lon":28.225233,
   "zone_id":"",
   "stop_url":"",
   "location_type":"0",
   "parent_station":"rhodesfield_station",
   "wheelchair_boarding":"1",
   "stop_timezone":""
 },
 {
   "stop_id":"rhodesfield_platform_we",
   "stop_code":"",
   "stop_name":"Rhodesfield Platform ",
   "stop_desc":"",
   "stop_lat":-26.128333,
   "stop_lon":28.225233,
   "zone_id":"",
   "stop_url":"",
   "location_type":"0",
   "parent_station":"rhodesfield_station",
   "wheelchair_boarding":"1",
   "stop_timezone":""
 },
 {
   "stop_id":"ortambo_platform_ew",
   "stop_code":"",
   "stop_name":"O.R. Tambo Platform ",
   "stop_desc":"",
   "stop_lat":-26.132933,
   "stop_lon":28.231567,
   "zone_id":"",
   "stop_url":"",
   "location_type":"0",
   "parent_station":"ortambo_station",
   "wheelchair_boarding":"1",
   "stop_timezone":""
 },
 {
   "stop_id":"ortambo_platform_we",
   "stop_code":"",
   "stop_name":"O.R. Tambo Platform ",
   "stop_desc":"",
   "stop_lat":-26.132933,
   "stop_lon":28.231567,
   "zone_id":"",
   "stop_url":"",
   "location_type":"0",
   "parent_station":"ortambo_station",
   "wheelchair_boarding":"1",
   "stop_timezone":""
 },
# Stops with blank stop_id ignored - this is a template
 {
   "stop_id":"",
   "stop_code":"",
   "stop_name":"",
   "stop_desc":"",
   "stop_lat":0,
   "stop_lon":0,
   "zone_id":"",
   "stop_url":"",
   "location_type":"0",
   "parent_station":"",
   "wheelchair_boarding":"",
   "stop_timezone":""
 }
]
##### End of stop config

#### Trips
# Common settings
stop_details_overwrite = { # for stop_times - applies to al trips for a stop_id
  'hatfield_bus' : {
     #'stop_headsign' : '',
     'pickup_type' : '0', 
     'drop_off_type' : '0',
  },
  'pretoria_bus' : {
     #'stop_headsign' : '',
     'pickup_type' : '0', 
     'drop_off_type' : '0',
  },
  'centurion_bus' : {
     #'stop_headsign' : '',
     'pickup_type' : '0', 
     'drop_off_type' : '0',
  },
  'midrand_bus' : {
     #'stop_headsign' : '',
     'pickup_type' : '0', 
     'drop_off_type' : '0',
  },
  'marlboro_bus' : { # Currently unused....
     #'stop_headsign' : '',
     'pickup_type' : '0', 
     'drop_off_type' : '0',
  },
  'sandton_bus' : {
     #'stop_headsign' : '',
     'pickup_type' : '0', 
     'drop_off_type' : '0',
  },
  'rosebank_bus' : {
     #'stop_headsign' : '',
     'pickup_type' : '0', 
     'drop_off_type' : '0',
  },
  'park_bus' : {
     #'stop_headsign' : '',
     'pickup_type' : '0', 
     'drop_off_type' : '0',
  },
  'rhodesfield_bus' : {
     #'stop_headsign' : '',
     'pickup_type' : '0', 
     'drop_off_type' : '0',
  },
}
#Bus
bus_trips = { # trip is named after route - this is applied to all trips
  '__avg_speed' : 30, # km/h - for calculationg times
  '__frequencies' : [
     { # Peak 1
       'service_id' : 'weekday',
       'headway_secs' : '720', # 12 min
       'start_time' : '05:30:00',
       'stop_time'  : '08:29:59',
     },
     { # Off-peak 1
       'service_id' : 'weekday',
       'headway_secs' : '1200', # 20 min
       'start_time' : '08:30:00',
       'stop_time'  : '15:59:59',
     },
     { # Peak 2
       'service_id' : 'weekday',
       'headway_secs' : '720', # 12 min
       'start_time' : '16:00:00',
       'stop_time'  : '18:59:59',
     },
     { # Off-peak 2
       'service_id' : 'weekday',
       'headway_secs' : '1200', # 20 min
       'start_time' : '19:00:00',
       'stop_time'  : '20:30:00',
     },
#     { # Weekend - no service currently
#       'service_id' : 'weekend',
#       'headway_secs' : '1800', # 30 min
#       'start_time' : '05:30:00',
#       'stop_time' : '20:30:00',
#     },
  ],
  '__stops' : { # default settings for stop_times
     #'arrival_time' : '',
     #'departure_time' : '',
     #'stop_id' : '',
     #'stop_sequence' : '',
     #'stop_headsign' : '',
     'pickup_type' : '0', 
     'drop_off_type' : '3', # TODO: overwrite per stop elsewhere
     #'shape_dist_travelled' : '',
  },
  #'service_id' : '', # found from frequencies list...
  #'route_id'   : '', # same as trip_id
  #'trip_headsign' : '', # based on route name
  #'trip_headsign' : 'Park Station',
  #'trip_short_name' : '', # Same as route_id
  'direction_id' : '0', # 0 - normal, 1 - reverse - busses only in one direction
  'block_id' : '', # not used for Gautrain
  #'shape_id' : '', # Same as route_id
  'wheelchair_accessible' : '1', # Every second trip actually
  'trip_bikes_allowed' : '0', # Folding bikes only on Gautrain / Busses
}
bus_per_trip = { # Per trip settings - overwrites settings in bus_trips if same name
  'H1' : { # route_id/trip_id is index
    '__terminal' : '', # Start / stop point
    '__avg_speed': 30, # Average speed - km/h
  },
  'H2' : { # route_id/trip_id is index
    '__terminal' : '', # Start / stop point
    '__avg_speed': 30, # Average speed - km/h
  },
  'H3' : { # route_id/trip_id is index
    '__terminal' : '', # Start / stop point
    '__avg_speed': 30, # Average speed - km/h
  },
  'H4' : { # route_id/trip_id is index
    '__terminal' : '', # Start / stop point
    '__avg_speed': 30, # Average speed - km/h
  },
  'H5' : { # route_id/trip_id is index
    '__terminal' : '', # Start / stop point
    '__avg_speed': 30, # Average speed - km/h
  },
  'P1' : { # route_id/trip_id is index
    '__terminal' : '', # Start / stop point
    '__avg_speed': 30, # Average speed - km/h
  },
  'P2' : { # route_id/trip_id is index
    '__terminal' : '', # Start / stop point
    '__avg_speed': 30, # Average speed - km/h
  },
  'C1' : { # route_id/trip_id is index
    '__terminal' : '', # Start / stop point
    '__avg_speed': 30, # Average speed - km/h
  },
  'C2' : { # route_id/trip_id is index
    '__terminal' : '', # Start / stop point
    '__avg_speed': 30, # Average speed - km/h
  },
  'C3' : { # route_id/trip_id is index
    '__terminal' : '', # Start / stop point
    '__avg_speed': 30, # Average speed - km/h
  },
  'C4' : { # route_id/trip_id is index
    '__terminal' : '', # Start / stop point
    '__avg_speed': 30, # Average speed - km/h
  },
  'M1' : { # route_id/trip_id is index
    '__terminal' : '', # Start / stop point
    '__avg_speed': 30, # Average speed - km/h
  },
  'M2' : { # route_id/trip_id is index
    '__terminal' : '', # Start / stop point
    '__avg_speed': 30, # Average speed - km/h
  },
  'M3' : { # route_id/trip_id is index
    '__terminal' : '', # Start / stop point
    '__avg_speed': 30, # Average speed - km/h
  },
  'S2' : { # route_id/trip_id is index
    '__terminal' : '', # Start / stop point
    '__avg_speed': 30, # Average speed - km/h
  },
  'S3' : { # route_id/trip_id is index
    '__terminal' : '', # Start / stop point
    '__avg_speed': 30, # Average speed - km/h
  },
  'S4' : { # route_id/trip_id is index
    '__terminal' : '', # Start / stop point
    '__avg_speed': 30, # Average speed - km/h
  },
  'S5' : { # route_id/trip_id is index
    '__terminal' : '', # Start / stop point
    '__avg_speed': 30, # Average speed - km/h
  },
  'RB1' : { # route_id/trip_id is index
    '__terminal' : '', # Start / stop point
    '__avg_speed': 30, # Average speed - km/h
  },
  'RB2' : { # route_id/trip_id is index
    '__terminal' : '', # Start / stop point
    '__avg_speed': 30, # Average speed - km/h
  },
  'RB3' : { # route_id/trip_id is index
    '__terminal' : '', # Start / stop point
    '__avg_speed': 30, # Average speed - km/h
  },
  'RB4' : { # route_id/trip_id is index
    '__terminal' : '', # Start / stop point
    '__avg_speed': 30, # Average speed - km/h
  },
  'RB5' : { # route_id/trip_id is index
    '__terminal' : '', # Start / stop point
    '__avg_speed': 30, # Average speed - km/h
  },
  'RF1' : { # route_id/trip_id is index
    '__terminal' : '', # Start / stop point
    '__avg_speed': 30, # Average speed - km/h
  },
#  '' : { # route_id/trip_id is index
#    '__terminal' : '', # Start / stop point
#    '__avg_speed': 30, # Average speed - km/h
#  },
}

#Train
train_trips = {
   'gautrain_ns_' : {
     'service_id' : 'weekday',
     'route_id'   : 'gautrain_ns',
     'trip_headsign' : 'Rosebank',
     #'trip_headsign' : 'Park Station',
     'trip_short_name' : '',
     'direction_id' : '0', # 0 - normal, 1 - reverse
     'block_id' : '',
     'shape_id' : 'gautrain_ns',
     'wheelchair_accessible' : '',
     'trip_bikes_allowed' : '',
     # Fields starting with __ is internal and not added directly to trips.txt
     '__stops' : {
       'order' : ['hatfield_platform_ns','pretoria_platform_ns','centurion_platform_ns','midrand_platform_ns','marlboro_platform_ns','sandton_platform_ns','rosebank_platform_ns'],
       #'order' : ['hatfield_station','pretoria_station','centurion_station','midrand_station','marlboro_station','sandton_station','rosebank_station','park_station']
       'time_taken' : [0,7,14,23,29,34,38],
       #'time_taken' : [0,7,14,23,29,34,38,42], # once park operational
       'start_times' : [ # departure time at first station
          # peak
          '0526','0538','0550',
          '0602','0614','0626','0638','0650',
          '0702','0714','0726','0738','0750',
          '0802','0814','0826',
          # off-peak
          '0844',
          '0904','0924','0944',
          '1004','1024','1044',
          '1104','1124','1144',
          '1204','1224','1244',
          '1304','1324','1344',
          '1404','1424','1444',
          '1504','1524','1544',
          # peak
          '1604','1616','1628','1640','1652',
          '1704','1716','1728','1740','1752',
          '1804','1816','1828','1840','1852',
          '1904','1916',
          # off-peak
          '1936','1956',
          '2016','2030',
       ]
     },
   },
   'gautrain_sn_' : {
     'service_id' : 'weekday',
     'route_id'   : 'gautrain_ns',
     'trip_headsign' : 'Hatfield',
     'trip_short_name' : '',
     'direction_id' : '1', # 0 - normal, 1 - reverse
     'block_id' : '',
     'shape_id' : 'gautrain_sn',
     'wheelchair_accessible' : '',
     'trip_bikes_allowed' : '',
     # Fields starting with __ is internal and not added directly to trips.txt
     '__stops' : {
       'order' : ['rosebank_platform_sn','sandton_platform_sn','marlboro_platform_sn','midrand_platform_sn','centurion_platform_sn','pretoria_platform_sn','hatfield_platform_sn'],
       #'order' : ['park_station','rosebank_station','sandton_station','marlboro_station','midrand_station','centurion_station','pretoria_station','hatfield_station'],
       'time_taken' : [4,8,12,18,27,35,42], # start times realtive to park
       #'time_taken' : [0,4,8,12,18,27,35,42],
       'start_times' : [ # departure time at first station - park in this case
          # peak
          '0524','0536','0548',
          '0600','0612','0624','0636','0648',
          '0700','0712','0724','0736','0748',
          '0800','0812','0824','0836','0848',
          # off-peak
          '0900','0918','0938','0958',
          '1018','1038','1058',
          '1118','1138','1158',
          '1218','1238','1258',
          '1318','1338','1358',
          '1418','1438','1458',
          '1518','1538','1550',
          # peak
          '1602','1614','1626','1638','1650',
          '1702','1714','1726','1738','1750',
          '1802','1814','1826','1838','1850',
          '1902','1914','1926','1938','1950',
          # off-peak
          '2010','2030',
       ]
     },
   },
   'gautrain_ew_' : {
     'service_id' : 'weekday',
     'route_id'   : 'gautrain_ew',
     'trip_headsign' : 'OR Tambo / Rhodesfield',
     'trip_short_name' : '',
     'direction_id' : '0', # 0 - normal, 1 - reverse
     'block_id' : '',
     'shape_id' : 'gautrain_ew',
     'wheelchair_accessible' : '',
     'trip_bikes_allowed' : '',
     # Fields starting with __ is internal and not added directly to trips.txt
     '__stops' : {
       'order' : ['ortambo_platform_ew','rhodesfield_platform_ew','marlboro_platform_ew','sandton_platform_ew'],
       'time_taken' : [0,2,9,13],
       'start_times' : [ # departure time at first station - park in this case
          # peak
          '0530','0542','0554',
          '0606','0618','0630','0642','0654',
          '0706','0718','0730','0742','0754',
          '0806','0818','0830','0842',
          # off-peak
          '0900','0920','0940',
          '1000','1020','1040',
          '1100','1120','1140',
          '1200','1220','1240',
          '1300','1320','1340',
          '1400','1420','1440',
          '1500','1520','1540','1556',
          # peak
          '1608','1620','1632','1644','1656',
          '1708','1720','1732','1744','1756',
          '1808','1820','1832','1844','1856',
          '1908','1920','1932','1950',
          # off-peak
          '2010','2030',
       ]
     },
   },
   'gautrain_we_' : {
     'service_id' : 'weekday',
     'route_id'   : 'gautrain_ew',
     'trip_headsign' : 'Sandton',
     'trip_short_name' : '',
     'direction_id' : '1', # 0 - normal, 1 - reverse
     'block_id' : '',
     'shape_id' : 'gautrain_we',
     'wheelchair_accessible' : '',
     'trip_bikes_allowed' : '',
     # Fields starting with __ is internal and not added directly to trips.txt
     '__stops' : {
       'order' : ['sandton_platform_we','marlboro_platform_we','rhodesfield_platform_we','ortambo_platform_we'],
       'time_taken' : [0,4,12,14],
       'start_times' : [ # departure time at first station - park in this case
          # peak
          '0524','0536','0548',
          '0600','0612','0624','0636','0648',
          '0700','0712','0724','0736','0748',
          '0800','0812','0824',
          # off-peak
          '0840',
          '0900','0920','0940',
          '1000','1020','1040',
          '1100','1120','1140',
          '1200','1220','1240',
          '1300','1320','1340',
          '1400','1420','1440',
          '1520','1538','1550',
          # peak
          '1602','1614','1626','1638','1650',
          '1702','1714','1726','1738','1750',
          '1802','1814','1826','1838','1850',
          # off-peak
          '1902','1914','1930','1950',
          '2010','2030',
       ]
     },
   },
}
default_train_trip = {
  'trip_id'        : '',
  'service_id'     : '',
  'route_id'       : '',
  'trip_headsign'  : '',
  'trip_short_name': '',
  'direction_id'   : '0', # 0 - normal, 1 - reverse
  'block_id'       : '',
  'shape_id'       : '',
  'wheelchair_accessible'  : '1',
  'trip_bikes_allowed'     : '0',
}
##### End of trip config

#### Shapes
# Array of arrays with these values: lat, lon - dist travelled to be calculated...
hardcoded_shapes =  { # Generated with getShapes.py from Gautrain_shapes.kml then reformatted and added here
  'gautrain_ew': [ ['-26.13232678143923', '28.23213468850645'],
                   ['-26.13159846617816', '28.22819887605944'],
                   ['-26.13051760421401', '28.22642056347319'],
                   ['-26.1288021434496', '28.2253813975553'],
                   ['-26.12605928552614', '28.2238728742888'],
                   ['-26.12483951637131', '28.22210259035236'],
                   ['-26.12341400208727', '28.21671761438485'],
                   ['-26.1167059885422', '28.20353650581327'],
                   ['-26.11047067889334', '28.19105844394624'],
                   ['-26.10372392035027', '28.18067619522978'],
                   ['-26.10168507353132', '28.17589252196958'],
                   ['-26.10076411078418', '28.16977843196693'],
                   ['-26.10021467737024', '28.16608384181424'],
                   ['-26.09527729015063', '28.15473515146166'],
                   ['-26.08370116426825', '28.13482324672954'],
                   ['-26.08154901096085', '28.12934334745892'],
                   ['-26.08087201621024', '28.12261930849046'],
                   ['-26.08156283374928', '28.11839505097027'],
                   ['-26.08375616464979', '28.10984645464064'],
                   ['-26.08542847754178', '28.10307088987695'],
                   ['-26.10791462528289', '28.05761145659118']],
  'gautrain_ns': [ ['-25.74727328722002', '28.23946302278673'],
                   ['-25.74759259741053', '28.23843777758771'],
                   ['-25.74821992221156', '28.23651908636387'],
                   ['-25.74898215222661', '28.23441919015241'],
                   ['-25.75027630201747', '28.23056798548762'],
                   ['-25.75060400793679', '28.22981943639159'],
                   ['-25.75125213456454', '28.22888544354944'],
                   ['-25.75201816428012', '28.22811669751545'],
                   ['-25.75363253865755', '28.22671735356595'],
                   ['-25.75589347389322', '28.22461600526892'],
                   ['-25.7585515241039', '28.22234140998085'],
                   ['-25.75942021476713', '28.22137139746403'],
                   ['-25.7597826465119', '28.2207535403125'],
                   ['-25.7600488311141', '28.22018865882832'],
                   ['-25.76018978371271', '28.21964439802384'],
                   ['-25.76026430647173', '28.21884557897961'],
                   ['-25.76017183345312', '28.21792542365807'],
                   ['-25.76004422488378', '28.2169807600717'],
                   ['-25.75975437396297', '28.21550303742056'],
                   ['-25.75972116809227', '28.21490698762545'],
                   ['-25.75980425937066', '28.21437948634403'],
                   ['-25.76020656074578', '28.2132633834302'],
                   ['-25.760577846252', '28.21227322968942'],
                   ['-25.76068853181744', '28.21186673903181'],
                   ['-25.76074416071493', '28.21138157700004'],
                   ['-25.7607080376735', '28.21043813428361'],
                   ['-25.75974379277808', '28.20314472103655'],
                   ['-25.75977393834531', '28.20214455659789'],
                   ['-25.76005199029316', '28.20112812440789'],
                   ['-25.7612352121127', '28.199558233885'],
                   ['-25.76320993496207', '28.19724056935837'],
                   ['-25.76389602447209', '28.19579765867178'],
                   ['-25.76382644102168', '28.19455343351871'],
                   ['-25.76348134958545', '28.19382180118109'],
                   ['-25.76301955780853', '28.19326212028899'],
                   ['-25.76221645661773', '28.1926431231886'],
                   ['-25.76098793962634', '28.19154352520039'],
                   ['-25.76289578752407', '28.19304992294636'],
                   ['-25.76349784168001', '28.19337677053453'],
                   ['-25.76390276354897', '28.19352792508202'],
                   ['-25.76476369154579', '28.19351814640447'],
                   ['-25.76622295674235', '28.19330258708002'],
                   ['-25.7670685874154', '28.19318849515854'],
                   ['-25.76934231071023', '28.19307648913982'],
                   ['-25.77058751803361', '28.19296057582226'],
                   ['-25.77305419388597', '28.19305963342641'],
                   ['-25.77380736375365', '28.19297685002845'],
                   ['-25.77428514363568', '28.19288362202683'],
                   ['-25.77488369725544', '28.19273417645242'],
                   ['-25.77694193808275', '28.19208619104499'],
                   ['-25.77818741432371', '28.19161768027885'],
                   ['-25.78087048957271', '28.19062194214011'],
                   ['-25.78166614252877', '28.19034570516245'],
                   ['-25.78767877072391', '28.18788733177625'],
                   ['-25.78978545122076', '28.18592980917106'],
                   ['-25.79185467937972', '28.1832680143986'],
                   ['-25.79379618424815', '28.18143304568938'],
                   ['-25.79621741675782', '28.18019530168125'],
                   ['-25.79872120328484', '28.17958946837808'],
                   ['-25.81327140482095', '28.17992978028182'],
                   ['-25.82287007220273', '28.18048963568065'],
                   ['-25.83221222277189', '28.18321677051576'],
                   ['-25.83671468214805', '28.18385194008997'],
                   ['-25.84346339328718', '28.18488642697401'],
                   ['-25.84579328185212', '28.18559751242316'],
                   ['-25.84765783305832', '28.1865071595045'],
                   ['-25.85124418736538', '28.18908739396257'],
                   ['-25.85360097219603', '28.1908422167302'],
                   ['-25.8573874458732', '28.19306601313991'],
                   ['-25.86082229983438', '28.19361555859242'],
                   ['-25.86418918473656', '28.19297343090471'],
                   ['-25.86666758291373', '28.19154949555578'],
                   ['-25.86855215229874', '28.18969561925256'],
                   ['-25.87069117301036', '28.1858772728352'],
                   ['-25.87467900479492', '28.17709407791816'],
                   ['-25.87619076122243', '28.17428368492832'],
                   ['-25.87859377115296', '28.17134271383015'],
                   ['-25.88137624624958', '28.16921402976712'],
                   ['-25.88270205766159', '28.16853990109506'],
                   ['-25.89282066897359', '28.16555573199566'],
                   ['-25.90433116045506', '28.1624260206387'],
                   ['-25.90968843708574', '28.16099064845778'],
                   ['-25.91539670213346', '28.15862821784955'],
                   ['-25.91690533751659', '28.15771296123099'],
                   ['-25.92147439634087', '28.15474227153118'],
                   ['-25.92615269842165', '28.15185590336553'],
                   ['-25.92946434969629', '28.14980117635319'],
                   ['-25.93370760664109', '28.14827628592088'],
                   ['-25.94082537438066', '28.14580463354734'],
                   ['-25.95010585737125', '28.14248796635217'],
                   ['-25.95684601466101', '28.14080877560563'],
                   ['-25.9778896409795', '28.13505253886943'],
                   ['-25.98436875368892', '28.13291222947147'],
                   ['-25.98745784228649', '28.13262591371813'],
                   ['-25.98954573269587', '28.1328860596941'],
                   ['-25.99115886361632', '28.13327578321737'],
                   ['-25.99528853551454', '28.13519848095048'],
                   ['-25.99881176971511', '28.13685576042542'],
                   ['-25.99997231348065', '28.13730645306034'],
                   ['-26.0007888779529', '28.13751446876056'],
                   ['-26.0032097078981', '28.13765536583188'],
                   ['-26.00534316312295', '28.1370472305416'],
                   ['-26.00898868498119', '28.13539584223723'],
                   ['-26.01313244666678', '28.13232568166095'],
                   ['-26.01628798655951', '28.13013557913103'],
                   ['-26.01998778835531', '28.12889903872122'],
                   ['-26.02394191823003', '28.12837343203351'],
                   ['-26.02960307121471', '28.12650885836755'],
                   ['-26.03446710265463', '28.12397120201905'],
                   ['-26.04065870542071', '28.12103260662887'],
                   ['-26.04462066334726', '28.12017814852252'],
                   ['-26.04932733868437', '28.12044532984661'],
                   ['-26.05449903279524', '28.12086376117395'],
                   ['-26.05884556773992', '28.11992276323626'],
                   ['-26.06213389320286', '28.11859951897873'],
                   ['-26.06567995315776', '28.11816343915496'],
                   ['-26.06981595250746', '28.11878083236401'],
                   ['-26.07347406308367', '28.11987191656806'],
                   ['-26.07748136552181', '28.12022297091922'],
                   ['-26.07957161441351', '28.1193012370823'],
                   ['-26.08148924018267', '28.11723617953692'],
                   ['-26.0834721213305', '28.11075728852114'],
                   ['-26.0852327647083', '28.10366338643003'],
                   ['-26.08675946480758', '28.10015020170497'],
                   ['-26.08763284949091', '28.09843714593837'],
                   ['-26.10758561313048', '28.05794743556962'],
                   ['-26.14197426257676', '28.04343700842688'],
                   ['-26.14478299590367', '28.04395665600539'],
                   ['-26.14900398097334', '28.04479006406153'],
                   ['-26.19836954898384', '28.04264294451009']]
}
# Shapes that are reverse versions of others
reverse_shapes = {
  'gautrain_sn' : 'gautrain_ns',
  'gautrain_we' : 'gautrain_ew',
}
# TODO: Shape Overwrites
##### End of shape config

#### TODO: Transfers
##### End of transfer config

#### TODO: Fares
##### End of fare config

################################ Useful functions #######################################
def unescape(s):
  a = re.sub('<[^>]+>','',s) # markup
  a = re.sub('&amp;','&',a)
  a = re.sub('&nbsp;','',a)
  a = re.sub('&[a-zA-Z]+;','',a) # unknown escapes
  return a
# See also pydoc transitfeed.shapelib and transitfeed.util
def distance(lat1, long1, lat2, long2): #http://www.johndcook.com/python_longitude_latitude.html
    # Convert latitude and longitude to 
    # spherical coordinates in radians.
    degrees_to_radians = math.pi/180.0
    # phi = 90 - latitude
    phi1 = (90.0 - lat1)*degrees_to_radians
    phi2 = (90.0 - lat2)*degrees_to_radians
    # theta = longitude
    theta1 = long1*degrees_to_radians
    theta2 = long2*degrees_to_radians
    # Compute spherical distance from spherical coordinates.
    # For two locations in spherical coordinates 
    # (1, theta, phi) and (1, theta, phi)
    # cosine( arc length ) = 
    #    sin phi sin phi' cos(theta-theta') + cos phi cos phi'
    # distance = rho * arc length
    cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) + 
           math.cos(phi1)*math.cos(phi2))
    arc = math.acos( cos )
    # Remember to multiply arc by the radius of the earth 
    # in your favorite set of units to get length.
    return arc*6373
def bus_distance(lat1, long1, lat2, long2): # distance along edges, similar to city blocks
    return distance(lat1, long1, lat1, long2) + distance(lat1, long1, lat2, long1)
def time_to_int(time): # Convert a HHMM or HHMMSS time to seconds from midnight
  m1 = re.match(r"^(\d\d):?(\d\d)$",time)
  m2 = re.match(r"^(\d\d):?(\d\d):?(\d\d)$",time)
  if m1 :
    return int(m1.group(1))*3600 + int(m1.group(2))*60
  elif m2 :
    return int(m2.group(1))*3600 + int(m2.group(2))*60 + int(m2.group(3))
  else:
    print "Invalid time: ",time
    return None
  
################################ Code #######################################
# Code
# Create feed object
gtfs = transitfeed.Schedule()
# Add agencies TODO: Based on config
gtfs.NewDefaultAgency(agency_id="za_gautrain",agency_name="Gautrain Management Agency",agency_url="http://www.gautrain.co.za",agency_timezone="Africa/Johannesburg",agency_lang="en",agency_phone="0800 GAUTRAIN",agency_fare_url="http://www.gautraincard.co.za/",agency_acronym="GMA")

####### Calender handling
# ---Setup calendar
# Calender handling order:
#  weekend / weekday
#  holidays
#  no service
#  extra weekday
#  special service
# Weekday
weekday_srv = transitfeed.ServicePeriod()
weekday_srv.SetServiceId("weekday")
weekday_srv.SetWeekendService(False)
weekday_srv.SetWeekdayService(True)
weekday_srv.SetStartDate(cal_start)
weekday_srv.SetEndDate(cal_end)
# Weekend
weekend_srv = transitfeed.ServicePeriod()
weekend_srv.SetServiceId("weekend")
weekend_srv.SetWeekendService(True)
weekend_srv.SetWeekdayService(False)
weekend_srv.SetStartDate(cal_start)
weekend_srv.SetEndDate(cal_end)
#
# Handle public holidays
for date in cal_holiday:
  weekday_srv.SetDateHasService(date,False)
  weekend_srv.SetDateHasService(date,True)
# No service days
for date in cal_no_service:
  weekday_srv.SetDateHasService(date,False)
  weekend_srv.SetDateHasService(date,False)
# Extra weekday service
for date in cal_no_service:
  weekday_srv.SetDateHasService(date,True)
# TODO: Special service - service need to be created first...
#for entry in cal_special_service
#  
# Set up service dates in GTFS object
gtfs.SetDefaultServicePeriod(weekday_srv)
gtfs.AddServicePeriodObject(weekend_srv)

################## Network fetcher
# Retreive info from Gautrain site
conn = httplib.HTTPConnection("join.gautrain.co.za")
headers = {"Content-Type" : "application/json"}
conn.connect()
# routeType: 1 - Train, 2 - Bus
# Train route data mostly useless
#conn.request("POST","/map.aspx/GetAllRoutes", '{"routeType":"1","mapType":"Google"}', headers)
#trainroutesresp = conn.getresponse()
#print "Train routes request: ",trainroutesresp.status,trainroutesresp.reason
#if trainroutesresp.status == 200:
#  print "Reading data..."
#  trainroutesdata = json.load(trainroutesresp)
#  print "Done"
#else:
#  print "Error %s retrieving train routes data" % trainroutesresp.status
#  conn.close()
#  sys.exit(2)
#
conn.request("POST","/map.aspx/GetAllRoutes", '{"routeType":"2","mapType":"Google"}', headers)
busroutesresp = conn.getresponse()
print "Bus routes request: ",busroutesresp.status,busroutesresp.reason
if busroutesresp.status == 200:
  print "Reading data..."
  busroutesdata = json.load(busroutesresp)
  print "Done"
else:
  print "Error %s retrieving routes data" % routesresp.status
  conn.close()
  sys.exit(2)
#
conn.request("POST","/map.aspx/GetStations", "{}", headers)
stationsresp = conn.getresponse()
print "Stations request: ",stationsresp.status,stationsresp.reason
if stationsresp.status == 200:
  print "Reading data..."
  stationsdata = json.load(stationsresp)
  print "Done"
else:
  print "Error %s retrieving stations data" % stationsresp.status
  conn.close()
  sys.exit(2)
conn.close()
#
# Extract real data
busroutes = json.loads(busroutesdata["d"]) # Returns a list
#trainroutes = json.loads(trainroutesdata["d"]) # Returns a list
#allroutes = busroutes[:],trainroutes[:]
allroutes = busroutes[:]
stations = json.loads(stationsdata["d"]) # Returns a list
######## End fetch

# Dump data examples for debug purposes
if debug:
#  print "Train Route data:"
#  print "-----------------"
#  print len(trainroutes)
#  print trainroutes[0]
#  print
  print "Bus Route data:"
  print "---------------"
  print len(busroutes)
  print busroutes[0]
  print
  print "Station data:"
  print "-------------"
  print len(stations)
  print stations[0]

####### STOPS
# Processing order:
# Fetched data - stations array
# stop_delete processed
# Defaults populated - if debug, messages for values already present
# Links and descriptions added to overwrites
# Overrides done - message if target missing
# hardcoded stops added - print message if already defined and skip
stops = dict() # Has stop_id as key, object as value
# Process fetched data
for stop in stations:
  #print stop["sName"],stop["sTerminus"],stop["sDescription"],stop["sLatLng"],stop["sID"]
  stop_id = stop["sName"]
  if re.search("\s",stop_id): stop_id = stop_id.lower() # Don't mess around with case if no whitespace
  stop_id = re.sub(r'\W','_',stop_id) # Turn all non-word chars to underscores (including dashes)
  if re.search("^[A-Z][A-Za-z]*\d[-_]\d+$",stop["sName"]):
    stop_code = stop["sName"]
  else:
    stop_code = ''
  stop_name = re.sub('oerskool',u'oërskool',unescape(stop["sDescription"])) # Get rid of HTML and fix spelling
  stop_lat , stop_lon = re.sub(r'[^\d\.\-,]','',stop["sLatLng"]).split(',') # Clean and split
  stop_fields = {
     "stop_id":stop_id,
     "stop_code":stop_code,
     "stop_name":stop_name,
     "stop_desc":"",
     "stop_lat":stop_lat,
     "stop_lon":stop_lon,
     "zone_id":"",
     "stop_url":"",
     "location_type":"",
     "parent_station":"",
     "wheelchair_boarding":"",
     "stop_timezone":""
  }
  stops[stop_id] = transitfeed.Stop(field_dict=stop_fields)
  if debug: print "Created stop: ", stop_id
# Delete stops in stop_delete
for stop_id in stop_delete:
  del stops[stop_id]
  if debug : print "Deleted ",stop_id
# Set up default values
for stop in stops.values():
  for field in stop.keys():
    if (default_stop[field] != '' and stop[field] == ''):
      if debug : print "Setting default",field,"for",stop["stop_id"],"to",default_stop[field]
      stop.__setattr__(field,default_stop[field])
    elif debug and stop[field] != '' and default_stop[field] != '':
      print field,"is already set to non-default value for",stop["stop_id"]
# Add URL links to overrides
for stop_id in stop_link.keys():
  if not (stop_id in stop_overwrite.keys()):
    stop_overwrite[stop_id] = {"order":99999}
  if "stop_url" in stop_overwrite[stop_id].keys():
    print "Warning:",stop_id,"already have a stop_url override. skipping...."
    continue
  stop_overwrite[stop_id]["stop_url"] = stop_link[stop_id]
# Add descriptions to overrides
for stop_id in stop_describe.keys():
  if not (stop_id in stop_overwrite.keys()):
    stop_overwrite[stop_id] = {"order":99999}
  if "stop_desc" in stop_overwrite[stop_id].keys():
    print "Warning:",stop_id,"already have a stop_desc override. skipping...."
    continue
  stop_overwrite[stop_id]["stop_desc"] = stop_describe[stop_id]
# Process overrides
# Get set of order values
orders = array.array('i')
for change in stop_overwrite.values():
  if orders.count(change["order"]) == 0:
    orders.extend([change["order"]]) # deduplicate orders
# Do changes, run through orders in increasing order
for order in sorted(orders):
  for stop_id in stop_overwrite.keys():
    if stop_overwrite[stop_id]["order"] == order:
      if not ( stop_id in stops.keys() ):
        print "Invalid overwrite for", stop_id,"! Stop doesn't exist"
        continue
      del stop_overwrite[stop_id]["order"] # delete order
      ostop_id = stop_id # backup in case it is changed
      if "stop_id" in stop_overwrite[ostop_id]:  # Need special handling
        field = "stop_id"
        old_val = stops[stop_id][field]
        if debug : print ostop_id,field, ":",old_val,"->",stop_overwrite[ostop_id][field]
        stop_id = stop_overwrite[ostop_id]["stop_id"]
        stops[ostop_id].__setattr__('stop_id',stop_id)
        stops[stop_id] = stops[ostop_id]
        del stop_overwrite[ostop_id][field] 
        del stops[ostop_id]
      for field in stop_overwrite[ostop_id].keys():
        if field in stops[stop_id].keys(): # won't create new fields here, add to defaults if that is needed
          old_val = stops[stop_id][field]
          #stops[stop_id][field] = stop_overwrite[ostop_id][field]
          stops[stop_id].__setattr__(field,stop_overwrite[ostop_id][field])
          if debug : print stop_id,field, ":",old_val,"->",stop_overwrite[ostop_id][field]
        else:
          print "Invalid overwrite for ", stop_id," field ",field
        del stop_overwrite[ostop_id][field] 
      del stop_overwrite[ostop_id]
    else:
      continue
# Add hardcoded stops
for new_stop in hardcoded_stops:
  if new_stop["stop_id"] == '' or new_stop["stop_id"] == None: continue
  stops[new_stop["stop_id"]] = transitfeed.Stop(field_dict=new_stop)
  if debug: print "Created stop: ", new_stop["stop_id"]
# Actually add stops to feed
for stop in stops.values():
  gtfs.AddStopObject(stop)

####### ROUTES
# Processing order:
# Fetched data - busroutes array
# route_delete processed
# Defaults populated - if debug, messages for values already present
# Overrides done - message if target missing
# links added - must be blank beforehand
# description added - must be blank beforehand
# hardcoded routes added - print message if already defined and skip
# Routes from busroutes, trainroutes
routes = {}
# Fetched data - busroutes array
for route in busroutes:
  if route["rType"] == 2: # Bus
    route_type = 3
    generic_service_name = 'Gautrain Bus'
    route_id = route["rRouteName"].split(':',1)[0] # Only works for bus routes
    route_short_name = route_id
    route_long_name = route["rRouteName"].split(':',1)[1].title()
    # Shape
    shape = transitfeed.Shape(route_id) # For busroute, shape_id is route_id
    for points in route["rRouteData"].split("~"):
      try:
        if re.match("^-?\d+(\.\d+)?,-?\d+(\.\d+)?$",points):
          shape_pt_lat,shape_pt_lon = points.split(",")
          #dist = # TODO: Travelled distance
          shape.AddPoint(shape_pt_lat,shape_pt_lon)
          #shape.AddPoint(shape_pt_lat,shape_pt_lon,dist)
        else:
          if debug: print points,"is invalid, for route",route_id
      except:
        print "Error decoding ",points
        continue
    gtfs.AddShapeObject(shape)
  elif route["rType"] == 1: # Bus
    route_type = 2
    generic_service_name = 'Gautrain'
    print "Route type train unsupported"
    continue
  else:
    print "Unknown route type",route["rType"]
    continue
  route_color = route["rRouteColour"].upper()
  route_fields = {
    "route_id"             :route_id,
    "agency_id"            :"",
    "route_short_name"     :route_short_name,
    "route_long_name"      :route_long_name,
    "route_desc"           :"", # see route_describe
    "route_type"           :route_type,
    "route_url"            :"", # see route_link
    "route_color"          :route_color,
    "route_text_color"     :"",
    "generic_service_name" :""
  }
  routes[route_id] = transitfeed.Route(field_dict=route_fields)
  if debug: print "Created route: ", route_id
# route_delete processed
for route_id in route_delete:
  del routes[route_id]
  if debug : print "Deleted ",route_id
# Defaults populated - if debug, messages for values already present
for route in routes.values():
  for field in route.keys():
    if (default_route[field] != '' and route[field] == ''):
      if debug : print "Setting default",field,"for",route["route_id"],"to",default_route[field]
      route.__setattr__(field,default_route[field])
    elif debug and route[field] != '' and default_route[field] != '':
      print field,"is already set to non-default value for",route["route_id"]
# links,description added to overrides
# Add URL links to overrides
for route_id in route_link.keys():
  if not (route_id in route_overwrite.keys()):
    route_overwrite[route_id] = {"order":99999}
  if "route_url" in route_overwrite[route_id].keys():
    print "Warning:",route_id,"already have a route_url override. skipping...."
    continue
  route_overwrite[route_id]["route_url"] = route_link[route_id]
# Add descriptions to overrides
for route_id in route_describe.keys():
  if not (route_id in route_overwrite.keys()):
    route_overwrite[route_id] = {"order":99999}
  if "route_desc" in route_overwrite[route_id].keys():
    print "Warning:",route_id,"already have a route_desc override. skipping...."
    continue
  route_overwrite[route_id]["route_desc"] = route_describe[route_id]
# Overrides done - message if target missing
# Get set of order values
orders = array.array('i')
for change in route_overwrite.values():
  if orders.count(change["order"]) == 0:
    orders.extend([change["order"]]) # deduplicate orders
# Do changes, run through orders in increasing order
for order in sorted(orders):
  for route_id in route_overwrite.keys():
    if route_overwrite[route_id]["order"] == order:
      if not ( route_id in routes.keys() ):
        print "Invalid overwrite for", route_id,"! Route doesn't exist"
        continue
      del route_overwrite[route_id]["order"] # delete order
      oroute_id = route_id # backup in case it is changed
      if "route_id" in route_overwrite[oroute_id]:  # Need special handling
        field = "route_id"
        old_val = routes[route_id][field]
        if debug : print oroute_id,field, ":",old_val,"->",route_overwrite[oroute_id][field]
        route_id = route_overwrite[oroute_id]["route_id"]
        routes[oroute_id].__setattr__('route_id',route_id)
        routes[route_id] = routes[oroute_id]
        del route_overwrite[oroute_id][field] 
        del routes[oroute_id]
      for field in route_overwrite[oroute_id].keys():
        if field in routes[route_id].keys(): # won't create new fields here, add to defaults if that is needed
          old_val = routes[route_id][field]
          #routes[route_id][field] = route_overwrite[oroute_id][field]
          routes[route_id].__setattr__(field,route_overwrite[oroute_id][field])
          if debug : print route_id,field, ":",old_val,"->",route_overwrite[oroute_id][field]
        else:
          print "Invalid overwrite for ", route_id," field ",field
        del route_overwrite[oroute_id][field] 
      del route_overwrite[oroute_id]
    else:
      continue
# Handle hardcoded shapes
for shape_id in hardcoded_shapes.keys():
  if debug: print "Handling hardcoded shape",shape_id
  shape = transitfeed.Shape(shape_id)
  for point in hardcoded_shapes[shape_id]:
    shape.AddPoint(point[0],point[1])
  gtfs.AddShapeObject(shape)
for shape_id in reverse_shapes.keys():
  if debug: print "Handling shape reversal for",shape_id,"from",reverse_shapes[shape_id]
  orig = gtfs.GetShape(reverse_shapes[shape_id])
  shape = transitfeed.Shape(shape_id)
  for point in orig.points:
    shape.AddPoint(point[0],point[1])
  gtfs.AddShapeObject(shape)
# Add hardcoded routes
for new_route in hardcoded_routes:
  if new_route["route_id"] == '' or new_route["route_id"] == None: continue
  routes[new_route["route_id"]] = transitfeed.Route(field_dict=new_route)
  if debug: print "Created route: ", new_route["route_id"]
# Actually add routes to feed
for route in routes.values():
  gtfs.AddRouteObject(route)
# TODO: Handle hardcoded shapes & overrides

# Trips, stop_times and frequencies
# Trips: route_id,service_id,trip_id,trip_headsign,trip_short_name,direction_id,block_id,shape_id,wheelchair_accessible,trip_bikes_allowed
# stop times: trip_id,arrival_time,departure_time,stop_id,stop_sequence,stop_headsign,pickup_type,drop_off_type,shape_dist_traveled
# Frequencies: trip_id,start_time,end_time,headway_secs,exact_times
trips = {}
# Train
for trip_group in train_trips.keys():
  if debug: print "Processing trip group ",trip_group
  shape_id = train_trips[trip_group]["shape_id"]
  for start_time in train_trips[trip_group]["__stops"]["start_times"]:
    trip_id = trip_group+start_time
    if debug: print "Handling trip",trip_id
    trip_hash = train_trips[trip_group].copy()
    tr_stops = trip_hash['__stops'].copy() # easier access
    trip_hash['trip_id'] = trip_id
    for field in trip_hash.keys(): # Delete values starting with __
      if re.match(r'__',field):
        del trip_hash[field]
    # TODO: Handle defaults
    # TODO: Create trip here
    trip = transitfeed.Trip(field_dict=trip_hash)
    trips[trip_id] = trip
    gtfs.AddTripObject(trip)
    for station,offset in zip(tr_stops['order'],tr_stops['time_taken']):
      # TODO: Handle overwrites / defaults
      # TODO: Add stops here
      stop_time = time_to_int(start_time) + 60*offset
      trip.AddStopTime(stop=gtfs.GetStop(station),arrival_secs=stop_time,departure_secs=stop_time,pickup_type=1,drop_off_type=1)
# Bus
busroutes = {} # list of busroutes
for route in gtfs.GetRouteList():
  if route['route_type'] == '3':
    busroutes[route['route_id']] = []
for stop in gtfs.GetStopList():
  for route in busroutes.keys():
    m = re.match('%s_' % route.upper(),stop['stop_id'].upper())
    if m:
      busroutes[route].append(stop['stop_id'])
      if debug: print 'Stop',stop['stop_id'],'in route',route
for route in busroutes.keys():
  # sort stops in numerical order
  busroutes[route] = sorted(busroutes[route],key=lambda route_id : int(route_id.split('_')[1]))
  trip_hash = {
    'route_id'   : route,
    'service_id' : 'weekday', # TODO: Handle properly
    'trip_id' : route,
    'trip_headsign' : gtfs.GetRoute(route)['route_name'],
    'trip_short_name' : route,
    'direction_id' : '0',
    'shape_id' : route,
  }
  trip = transitfeed.Trip(field_dict=trip_hash)
  trips[trip_id] = trip
  gtfs.AddTripObject(trip)
  i = 0
  for stop in busroutes[route]:
    stop_time = i*60 # TODO: Handle
    trip.AddStopTime(stop=gtfs.GetStop(stop),arrival_secs=stop_time,departure_secs=stop_time,pickup_type=1,drop_off_type=1)
    i += 1
  trip.AddFrequency('05:30:00','20:30:00',1200) # TODO

#gtfs.Validate()
gtfs.WriteGoogleTransitFeed("gautrain_unofficial.zip")
print "Done... If this is printed, script completed"
