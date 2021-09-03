trip planner log .csv data dictionary
=====================================
###### September 3rd, 2021

### This is an example .csv output:
     ip_hash,app_name,url,date,modes,companies,from,to
     b8473149d1430af08beabc55e767abcad05ef413,API (developer.trimet.org),"/prod?fromPlace=45.60%2C-122.74&toPlace=45.51%2C-122.67&mode=TRANSIT,WALK&time=11:30%20AM&date=09-01-21&companies=Uber",2021-09-01 00:16:17,"BUS,RAIL",Uber,"45.60,-122.74","45.51,-122.67"

#### ip_hash: 
ip_hash is a way to link requests from 'maybe' the same customer ... that said, a few of our apps are proxied (and thus the ip addresses are the same ... thus the hash is the same) -- I'll fix this eventually so it's more unique to better relate requests that appear to be coming from a similar source.

#### app_name:
app_name identifies which trimet app the request came from 

#### url:
url shows the GET request to the OpenTripPlanner (OTP) backend routing engine

#### date:
date is the datetime from Apache representing when the request was made.  The url also has a date and time param, which will often match that in the url.  But folks do occasionally plan a trip for a future time (and sometimes a past time).

#### modes:
modes is a simplification / human readable version of the mode param in the requested url. BUS and RAIL are the two transit modes you'll see in this string.  WALK is implied, and only shown when the trip request is WALK_ONLY.  BIKE, SCOOTER, CAR, which also have a companion _SHARE (e.g., BIKE_SHARE, SCOOTER_SHARE, CAR_SHARE) mode.   

#### companies:
companies is simply the param from the url ... should only see those for _SHARE mode requests. 

#### from:
lat,lon (e.g., the 'fromPlace' in the url) with any place/address name data stripped

#### to:
lat,lon (e.g., the 'toPlace' in the url) with any place/address name data stripped
