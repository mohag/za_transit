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
mv "$kmlfilename" "$kmlfilename.bak"
mv test.kml "$kmlfilename"
# TODO: Update version in feed
zip -u "$filename" -xi README CODE-LICENSE *.py *.sh validation-results.html feed_info.txt "$kmlfilename"
