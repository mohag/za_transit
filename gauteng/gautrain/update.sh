#!/bin/sh
filename=gautrain_unofficial.zip
kmlfilename=gautrain_unofficial.kml
./getRoutes.py
cd extracted
rm *.txt
unzip ../"$filename"
cd ..
feedvalidator.py -n "$filename"
kmlwriter.py "$filename"
./makeNiceKml.py # Still work in progress
zip -u "$filename" -xi README CODE-LICENSE *.py *.sh validation-results.html "$kmlfilename"
