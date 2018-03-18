# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START app]
import logging

from flask import Flask
from flask import request
from flask_cors import CORS
import requests

from requests_toolbelt.adapters import appengine
appengine.monkeypatch(validate_certificate=False)
import json
import math

from google.cloud import bigquery
bigquery_client = bigquery.Client('project-shubin')

GEOCODING_API_KEY = 'AIzaSyAdaCsSyIFSoyyvIyOQEobu1twZSiQ5K8o'

app = Flask(__name__)
CORS(app)
stations = []

##Open and read file
with open('ga_stations.json', 'r') as stations_file:
    content = stations_file.read()

    station_strings = content.split("\n")

    for station_string in station_strings:
    	stations.append(  json.loads(station_string) )


@app.route('/')
def hello():
    return json.dumps(stations)

def get_nearest_station(lat, lng):
	min_distance = None
	nearest_station = None
	bgn_dt = None
	end_dt = None
	for station in stations:
		distance = math.sqrt((float(station['lat']) - float(lat) )**2 + (float(station['lon']) - float(lng) )**2   )

		if min_distance == None:
			min_distance = distance
			nearest_station = station['usaf']
			bgn_dt = station['begin']
			end_dt = station['end']

		elif distance < min_distance:
			min_distance = distance
			nearest_station = station['usaf']
			bgn_dt = station['begin']
			end_dt = station['end']

	return (nearest_station, bgn_dt, end_dt)



@app.route('/nearest_station')
def get_nearest_station_by_lat_and_lon():
	place = request.args.get('place')

	params = {"address": place, "key": GEOCODING_API_KEY}

	geocode_resp = requests.get('https://maps.googleapis.com/maps/api/geocode/json', params=params)


	location = geocode_resp.json()


	lat = location['results'][0]['geometry']['location']['lat']
	lng = location['results'][0]['geometry']['location']['lng']

	nearest_station = get_nearest_station(lat, lng)

	return json.dumps( {"station" : nearest_station[0] } )


@app.route('/rainy_day_graph')
def get_rainy_day_graph():
	station = request.args.get('station')
	sql = '''SELECT mo as month, sum(cast(rain_drizzle as INT64)  )/count(*) as days_with_rain_percent FROM `bigquery-public-data.noaa_gsod.gsod20*`  where stn= "{station}" AND _TABLE_SUFFIX BETWEEN '10' AND '18' group by 1 order by cast(mo as int64) asc'''.format(station=station)

	QUERY = (sql)
	query_job = bigquery_client.query(QUERY)
	
	iterator = query_job.result(timeout=3000)
	rows = list(iterator)

	series_data = []

	for row in rows:

		series_data.append(row[1])


	return json.dumps(series_data)


@app.route('/solar_charts')
def get_solar_charts():
	lat = request.args.get('lat')
	station = request.args.get('station')
	sql = '''SELECT * FROM `bigquery-public-data.sunroof_solar.solar_potential_by_censustract`
where lat_max > {lat} and lat_min < {lat} and lng_min < {lng} and lng_max > {lng}
'''.format(lat=lat, lng=lng)




	


@app.errorhandler(500)
def server_error(e):
    # Log the error and stacktrace.
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500
# [END app]
