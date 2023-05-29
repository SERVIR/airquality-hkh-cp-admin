import json
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from django.http.response import JsonResponse
from rest_framework.response import Response

from AqApp.models import Site, Pollutant, PolluantData, LocationData
from AqApp.serializers import SiteSerializer, PollutantSerializer, PollutantPropertySerializer
from rest_framework.views import APIView
from rest_framework import status
# from django.contrib.gis.measure import D
# from django.contrib.gis.geos import *
from django.db.models import F
from django.db.models.functions import ACos, Cos, Radians, Sin
import http.client
import json
import xmltodict
import concurrent.futures
import urllib.request
from datetime import datetime

@csrf_exempt
def site_api(request, id=0):
    if request.method == "GET" and id == 0:
        sites = Site.objects.all()
        site_serializer = SiteSerializer(sites, many=True)
        return JsonResponse(site_serializer.data, safe=False)
    
    elif request.method == "GET" and id != 0:
        try:
            site = Site.objects.filter(station_id=id).values()
            site_serializer = SiteSerializer(site)
        except Exception:
            return JsonResponse({"code": "4000", "message": "site does not exist", "site": {site}})
        site_serializer = SiteSerializer(site, many=True)
        return JsonResponse(site_serializer.data, safe=False)
    
    elif request.method == "POST":
        site_data = JSONParser().parse(request)
        site_serializer = SiteSerializer(data=site_data)
        if site_serializer.is_valid():
            site_serializer.save()
            return JsonResponse("Added Successfully", safe=False)
        return JsonResponse("Failed to Add", safe=False)
    
    elif request.method == "PUT":
        site_data = JSONParser().parse(request)
        site = Site.objects.get(station_id=site_data['station_id'])
        site_serializer = SiteSerializer(site, data=site_data)
        if site_serializer.is_valid():
            site_serializer.save()
            return JsonResponse("Added Successfully", safe=False)
        return JsonResponse("Failed to Add", safe=False)
    
    elif request.method == "DELETE":
        site = Site.objects.get(station_id=id)
        site.delete()
        return JsonResponse("Deleted Successfully", safe=False)

@csrf_exempt
def pollutant_api(request, id=0):
    if request.method == "GET":
        pollutants = Pollutant.objects.all()
        pollutant_serializer = PollutantSerializer(pollutants, many=True)
        return JsonResponse(pollutant_serializer.data, safe=False)
    elif request.method == "GET"  and id != 0:
        try:
            pollutant = Pollutant.objects.filter(pollutant_id=id).values()
            pollutant_serializer = PollutantSerializer(pollutant)
        except Exception:
            return JsonResponse({"code": "4000", "message": "pollutant does not exist", "site": {site}})
        pollutant_serializer = PollutantSerializer(site, many=True)
        return JsonResponse(pollutant_serializer.data, safe=False)
    elif request.method == "POST":
        pollutant_data = JSONParser().parse(request)
        pollutant_serializer = PollutantSerializer(data=pollutant_data)
        if pollutant_serializer.is_valid():
            pollutant_serializer.save()
            return JsonResponse("Added Successfully", safe=False)
        return JsonResponse("Failed to Add", safe=False)
    elif request.method == "PUT":
        pollutant_data = JSONParser().parse(request)
        pollutant = Pollutant.objects.get(pollutant_id=pollutant_data['pollutant_id'])
        pollutant_serializer = PollutantSerializer(pollutant, data=pollutant_data)
        if pollutant_serializer.is_valid():
            pollutant_serializer.save()
            return JsonResponse("Added Successfully", safe=False)
        return JsonResponse("Failed to Add", safe=False)
    elif request.method == "DELETE":
        pollutant = Pollutant.objects.get(pollutant_id=id)
        pollutant.delete()
        return JsonResponse("Deleted Successfully", safe=False)


class PollutantDataAPIView(APIView):
    model = PolluantData

    def get(self, request, format=None):
        data = self.model.objects.filter(enabled=True).values()

        data = {
            "message" : "Pollutant data response.",
            "status" : status.HTTP_200_OK,
            "data" : data,
        }
        return Response(data, status.HTTP_200_OK)
    

class LocationDataAPIView(APIView):
    model = LocationData

    def get(self, request, format=None):
        data = self.model.objects.filter(enabled=True, saved_location=True).values(
                'pollutant__name', 
                'source', 
                'site', 
                'latitude',
                'longitude',
                'pollutant__id',
                'saved_location',
                'StId',
                'enabled',
                'id'
            )
        for rec in data:
            rec['id']  = rec['StId']
            if rec['source'] == "AIRNOW":
                rec['source'] = "AIR NOW"
            else:
                rec['source'] = "AERO NET"

        data = {
            "message" : "Location data response.",
            "status" : status.HTTP_200_OK,
            "data" : data,
        }
        return Response(data, status.HTTP_200_OK)


class LocationSourceDataAPIView(APIView):
    model = LocationData

    def get(self, request, source):
        if source == 'air_now':
            source = self.model.SOURCE.AIR_NOW
        else:
            source = self.model.SOURCE.AERO_NET

        data = self.model.objects.filter(source=source).values(
                'pollutant__name', 
                'source', 
                'site', 
                'latitude',
                'longitude',
                'pollutant__id',
                'saved_location',
                'StId',
                'enabled',
                'id'
            )
        
        for rec in data:
            rec['id']  = rec['StId']
            if rec['source'] == "AIRNOW":
                rec['source'] = "AIR NOW"
            else:
                rec['source'] = "AERO NET"

        data = {
            "message" : "Location data response.",
            "status" : status.HTTP_200_OK,
            "data" : data,
        }
        return Response(data, status.HTTP_200_OK)



from datetime import date
from datetime import timedelta
class NearestLocationAPIView(APIView):
    model = LocationData

    def post(self, request, format=None):
        lat = request.data.get('lat', None)
        long = request.data.get('long', None)
        if lat and long:
            data = self.model.objects.filter(source=LocationData.SOURCE.AIR_NOW).annotate(
            distance_miles = ACos(
                    Cos(
                        Radians(lat)
                    ) * Cos(
                        Radians(F('latitude'))
                    ) * Cos(
                        Radians(F('longitude')) - Radians(long)
                    ) + Sin(
                        Radians(lat)
                    ) * Sin(Radians(F('latitude')))
                ) * 3959
            ).order_by('distance_miles')[:3]

            pollutant_data = data.values(
                    'pollutant__name',
                    'source', 
                    'site', 
                    'latitude',
                    'longitude',
                    'pollutant__id',
                    'saved_location',
                    'StId',
                    'enabled',
                    'id'
                )

            # count = 0
            # for url in pollutant_data:
            #     res = self.process_pollutants_data(url)
            #     pollutant_data[count]['geos'] = res
            #     count = count + 1
            geos_data = {}
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                # Start the load operations and mark each future with its URL
                future_to_url = {executor.submit(self.process_pollutants_data, url): url for url in pollutant_data}
                count = 0
                for future in concurrent.futures.as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        data = future.result()
                        # pollutant_data[count]['geos'] = data
                        geos_data.update(data)
                        # count = count + 1
                    except Exception as exc:
                        print('%r generated an exception: %s' % (url, exc))
                    else:
                        print('%r page is %d bytes' % (url, len(data)))

            for data in pollutant_data:
                data['geos'] = geos_data[data['site']]

            data = {
                "message" : "Location data response.",
                "status" : status.HTTP_200_OK,
                "data" : pollutant_data,
            }
            return Response(data, status.HTTP_200_OK)
        
        else:
            data = {
                "message" : "Location data response.",
                "status" : status.HTTP_200_OK,
                "data" : [],
            }
            return Response(data, status.HTTP_200_OK)
    
    # async def process_pollutants_data(self, data_res):
    def process_pollutants_data(self, data_res):
        res_data = []

        headers = {
            'Content-Type': 'application/json'
        }            
        pm_conn = http.client.HTTPConnection("smog.icimod.org")

        payload = json.dumps({
            "stId": data_res['StId'],
            "ModelClass": "UsEmbassyPm",
            "ModelClassDataList": "UsEmbassyDataList",
            "typeName": "pm",
            "StartDate": datetime.today().strftime('%Y-%m-%d'),
            "EndDate": f"{datetime.today().strftime('%Y-%m-%d')}-23-59"
        })

        pm_conn.request("POST", "/apps/airquality/getData/", payload, headers)
        res = pm_conn.getresponse()
        data = json.loads(res.read())

        res_data.append(
            {
                "name" : "PM2.5",
                "value" : data['SeriesData'][-1] if data['SeriesData'] else [0,0],
                "order" : 1,
                "site" : data_res['site']
            }
        )

        pm_conn.close()

        geos_urls = [
            {
                "name" : "NO2/GEOS-NO2",
                "standart_name" : "NO2",
                "url": "http://smog.spatialapps.net:8080/thredds/catalog/HKHAirQualityWatch/RecentAndArchive/NO2/GEOS-NO2/catalog.xml",
                "order" : 2
            },
            {
                "name" : "CO/GEOS-CO",
                "standart_name" : "CO",
                "url": "http://smog.spatialapps.net:8080/thredds/catalog/HKHAirQualityWatch/RecentAndArchive/CO/GEOS-CO/catalog.xml",
                "order" : 3
            },
            {
                "name" : "O3/GEOS-O3",
                "standart_name" : "O3",
                "url": "http://smog.spatialapps.net:8080/thredds/catalog/HKHAirQualityWatch/RecentAndArchive/O3/GEOS-O3/catalog.xml",
                "order" : 4
            },
            {
                "name" : "SO2/GEOS-SO2",
                "standart_name" : "SO2",
                "url":"http://smog.spatialapps.net:8080/thredds/catalog/HKHAirQualityWatch/RecentAndArchive/SO2/GEOS-SO2/catalog.xml",
                "order" : 5
            },
        ]

        today = date.today()
        yesterday = today - timedelta(days = 7)
        yesterday = yesterday.strftime('%Y-%m-%d')
        today = today.strftime('%Y-%m-%d')

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Start the load operations and mark each future with its URL
            future_to_url = {executor.submit(self.get_value_of_points, geos, yesterday, today, data_res, headers): geos for geos in geos_urls}
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    data = future.result()
                    res_data.append(data)
                except Exception as exc:
                    print('%r generated an exception: %s' % (url, exc))
                else:
                    print('%r page is %d bytes' % (url, len(data)))

        res_data.sort(key=lambda x: x.get('order'))
        for res in res_data:
            del res['order']
            del res['site']
        return {data_res['site'] : res_data}



    def get_value_of_points(self, geos, yesterday, today, data_res, headers):
        conn = http.client.HTTPConnection("smog.icimod.org")
        payload = json.dumps({
            "url": geos['url'],
            "data_ext": ".nc",
            "startDate": yesterday,
            "endDate": today,
        })

        conn.request("POST", "/apps/airquality/slicedfromcatalog/", payload, headers)
        res = conn.getresponse()
        data = json.loads(res.read())

        # Second api calling.
        
        initial_data = f"HKHAirQualityWatch/RecentAndArchive/{geos['name']}/"
        if data['data']:
            data_dir = [f"{initial_data}{data['data'][-1]}"]

            payload = json.dumps({
                "DATADIR": data_dir,
                "LAYER": geos['standart_name'],
                "wkt": f"POINT({data_res['latitude']} {data_res['longitude']})",
                "type": "Point"
            })

            conn.request("POST", "/apps/airquality/timeseriesmodeldata/", payload, headers)
            timeseriesmodeldata_res = conn.getresponse()
            timeseriesmodeldata_data = json.loads(timeseriesmodeldata_res.read())

            # for (data_list, timeseriesmodeldata_list) in zip(data, timeseriesmodeldata_data['SeriesData']):
            return {
                    "name" : geos['standart_name'],
                    "value" : timeseriesmodeldata_data['SeriesData'][0],
                    "site" : data_res['site'],
                    "order": geos['order'],
                }
        else:
            return {
                    "name" : geos['standart_name'],
                    "value" : [0,0],
                    "site" : data_res['site'],
                    "order": geos['order'],
                }


class SliceFromCatagLog(APIView):

    def post(self, request, *args, **kwargs):
        conn = http.client.HTTPConnection("smog.icimod.org")
        payload = json.dumps({
            "url": "http://smog.spatialapps.net:8080/thredds/catalog/HKHAirQualityWatch/RecentAndArchive/NO2/GEOS-NO2/catalog.xml",
            "data_ext": ".nc",
            "startDate": "2023-04-02",
            "endDate": "2023-04-03"
        })
        headers = {
        'Content-Type': 'application/json'
        }
        conn.request("POST", "/apps/airquality/slicedfromcatalog/", payload, headers)
        res = conn.getresponse()
        data = json.loads(res.read())['data']

        # Second api calling.
        
        initial_data = "HKHAirQualityWatch/RecentAndArchive/NO2/GEOS-NO2/"
        data_dir = [f"{initial_data}{res}" for res in data]

        payload = json.dumps({
            "DATADIR": data_dir,
            "LAYER": "NO2",
            "wkt": "POINT(85.32635965396277 27.705769331276286)",
            "type": "Point"
        })

        conn.request("POST", "/apps/airquality/timeseriesmodeldata/", payload, headers)
        timeseriesmodeldata_res = conn.getresponse()
        timeseriesmodeldata_data = json.loads(timeseriesmodeldata_res.read())

        res_data = []
        for (data_list, timeseriesmodeldata_list) in zip(data, timeseriesmodeldata_data['SeriesData']):
            res_data.append(
                {
                    "data" : data_list,
                    "series_data" : timeseriesmodeldata_list,
                    "XaxisLabel": timeseriesmodeldata_data['XaxisLabel'],
                    "geom" : timeseriesmodeldata_data['geom']
                }
            )

        data = {
            "message" : "response.",
            "status" : status.HTTP_200_OK,
            "data" : res_data,
        }
        return Response(data, status.HTTP_200_OK)


class NearestLocationOfForcastAPIView(APIView):
    model = LocationData

    def post(self, request, format=None):
        lat = request.data.get('lat', None)
        long = request.data.get('long', None)
        if lat and long:
            data = self.model.objects.filter(source=LocationData.SOURCE.AIR_NOW).annotate(
            distance_miles = ACos(
                    Cos(
                        Radians(lat)
                    ) * Cos(
                        Radians(F('latitude'))
                    ) * Cos(
                        Radians(F('longitude')) - Radians(long)
                    ) + Sin(
                        Radians(lat)
                    ) * Sin(Radians(F('latitude')))
                ) * 3959
            ).order_by('distance_miles')[:3]

            pollutant_data = data.values(
                    'pollutant__name',
                    'source', 
                    'site', 
                    'latitude',
                    'longitude',
                    'pollutant__id',
                    'saved_location',
                    'StId',
                    'enabled',
                    'id'
                )

            # count = 0
            # for url in pollutant_data:
            #     res = self.process_pollutants_data(url)
            #     pollutant_data[count]['geos'] = res
            #     count = count + 1

            geos_data = {}
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                # Start the load operations and mark each future with its URL
                future_to_url = {executor.submit(self.process_pollutants_data, url): url for url in pollutant_data}
                count = 0
                for future in concurrent.futures.as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        data = future.result()
                        geos_data.update(data)
                        # count = count + 1
                    except Exception as exc:
                        print('%r generated an exception: %s' % (url, exc))
                    else:
                        print('%r page is %d bytes' % (url, len(data)))


            for data in pollutant_data:
                data['geos'] = geos_data[data['site']]

            data = {
                "message" : "Location data response.",
                "status" : status.HTTP_200_OK,
                "data" : pollutant_data,
            }
            return Response(data, status.HTTP_200_OK)
        
        else:
            data = {
                "message" : "Location data response.",
                "status" : status.HTTP_200_OK,
                "data" : [],
            }
            return Response(data, status.HTTP_200_OK)

    def process_pollutants_data(self, data_res):
        res_data = []

        headers = {
            'Content-Type': 'application/json'
        } 

        payload = ''
        base_endpoint = "/thredds/catalog/HKHAirQualityWatch/Forecast/WRF_Chem/d1_HKH/"
        conn = http.client.HTTPConnection("smog.spatialapps.net", 8080)
        conn.request("GET", f"{base_endpoint}catalog.json", payload, headers)
        res = conn.getresponse()
        data_dict = xmltodict.parse(res.read())
        last_date = data_dict['catalog']['dataset']['catalogRef'][-1]['@xlink:href']

        conn.request("GET", f"{base_endpoint}{last_date}", payload, headers)
        res = conn.getresponse()
        data_dict = xmltodict.parse(res.read())
        data_dir = [data_set['@ID'] for data_set in data_dict['catalog']['dataset']['dataset']]

        layers = [
            { 'name' : "PM2.5", "layer" : "PM25_SFC", 'order': 1},
            { 'name' : "O3", "layer" : "O3_TOTCOL", 'order': 2},
            { 'name' : "SO2", "layer" : "SO2_SFC", 'order': 3},
            { 'name' : "NO2", "layer" : "NO2_SFC", 'order': 4},
            { 'name' : "CO", "layer" : "CO_SFC", 'order': 5},
        ]

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Start the load operations and mark each future with its URL
            future_to_url = {executor.submit(self.get_value_of_points, layer, data_dir[-1], data_res, headers): layer for layer in layers}
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    data = future.result()
                    res_data.append(data)
                except Exception as exc:
                    print('%r generated an exception: %s' % (url, exc))
                else:
                    print('%r page is %d bytes' % (url, len(data)))

        res_data.sort(key=lambda x: x.get('order'))
        for res in res_data:
            del res['order']
            del res['site']
        return {data_res['site'] : res_data}


    def get_value_of_points(self, layer, data_dir, data_res, headers):
        conn = http.client.HTTPConnection("smog.icimod.org")

        payload = json.dumps({
            "DATADIR": [data_dir],
            "LAYER": layer['layer'],
            "type": "Point",
            "wkt": f"POINT({data_res['longitude']} {data_res['latitude']})",
        })

        conn.request("POST", "/apps/airquality/timeseriesmodeldata/", payload, headers)
        res = conn.getresponse()
        data = json.loads(res.read())
        data = data['SeriesData'][0] if data['SeriesData'] else [0.0, 0.0]
        if data:
            if data[0] == None:
                data[0] = 0.0
            if data[1] == None:
                data[1] = 0.0

        return {
            "name" : layer['name'],
            "value" : data,
            "order" : layer['order'],
            "site" : data_res['site'],
        }


class LocationOfForcastAPIView(APIView):

    def post(self, request, format=None):
        pollutant_data = request.data.get('points', [])
        # count = 0
        final_data = []
        # for url in pollutant_data:
        #     res = self.process_pollutants_data(url)
        #     # pollutant_data[count]['geos'] = res
        #     final_data.append({'lat' : url[0], 'long' : url[1], 'geos': res})
        #     count = count + 1

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Start the load operations and mark each future with its URL
            future_to_url = {executor.submit(self.process_pollutants_data, url): url for url in pollutant_data}
            count = 0
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    data = future.result()
                    final_data.append({'site' : url[2], 'latitude' : url[0], 'longitude' : url[1], 'geos': data[url[2]]})
                except Exception as exc:
                    print('%r generated an exception: %s' % (url, exc))
                else:
                    print('%r page is %d bytes' % (url, len(data)))

        data = {
            "message" : "Location data response.",
            "status" : status.HTTP_200_OK,
            "data" : final_data,
        }
        return Response(data, status.HTTP_200_OK)
        

    def process_pollutants_data(self, data_res):
        res_data = []

        headers = {
            'Content-Type': 'application/json'
        } 

        payload = ''
        base_endpoint = "/thredds/catalog/HKHAirQualityWatch/Forecast/WRF_Chem/d1_HKH/"
        conn = http.client.HTTPConnection("smog.icimod.org", 8080)
        conn.request("GET", f"{base_endpoint}catalog.json", payload, headers)
        res = conn.getresponse()
        data_dict = xmltodict.parse(res.read())
        last_date = data_dict['catalog']['dataset']['catalogRef'][-1]['@xlink:href']

        conn.request("GET", f"{base_endpoint}{last_date}", payload, headers)
        res = conn.getresponse()
        data_dict = xmltodict.parse(res.read())
        data_dir = [data_set['@ID'] for data_set in data_dict['catalog']['dataset']['dataset']]

        layers = [
            { 'name' : "PM2.5", "layer" : "PM25_SFC", "order" : 1},
            { 'name' : "O3", "layer" : "O3_TOTCOL", "order" : 2},
            { 'name' : "SO2", "layer" : "SO2_SFC", "order" : 3},
            { 'name' : "NO2", "layer" : "NO2_SFC", "order" : 4},
            { 'name' : "CO", "layer" : "CO_SFC", "order" : 5},
        ]

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Start the load operations and mark each future with its URL
            future_to_url = {executor.submit(self.get_value_of_points, layer, data_dir[-1], data_res, headers): layer for layer in layers}
            count = 0
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    data = future.result()
                    res_data.append(data)
                except Exception as exc:
                    print('%r generated an exception: %s' % (url, exc))
                else:
                    print('%r page is %d bytes' % (url, len(data)))

        res_data.sort(key=lambda x: x.get('order'))
        for res in res_data:
            del res['order']
            del res['site']
        return {data_res[2] : res_data}



    def get_value_of_points(self, layer, data_dir, data_res, headers):
        payload = json.dumps({
            "DATADIR": [data_dir],
            "LAYER": layer['layer'],
            "type": "Point",
            "wkt": f"POINT({data_res[1]} {data_res[0]})",
        })

        conn = http.client.HTTPConnection("smog.icimod.org")
        conn.request("POST", "/apps/airquality/timeseriesmodeldata/", payload, headers)

        res = conn.getresponse()
        data = json.loads(res.read())
        data = data['SeriesData'][0] if data['SeriesData'] else [0,0]
        if data:
            if data[0] == None:
                data[0] = 0.0
            if data[1] == None:
                data[1] = 0.0

        return{
            "name" : layer['name'],
            "value" : data,
            "site" : data_res[2],
            "order" : layer['order'],
        }


class RecentArchiveLocationAPIView(APIView):

    def post(self, request, format=None):
        pollutant_data = request.data.get('points', [])

        # count = 0
        final_data = []
        # for url in pollutant_data:
        #     res = self.process_pollutants_data(url)
        #     # pollutant_data[count]['geos'] = res
        #     final_data.append({'name' : url[2], 'lat' : url[0], 'long' : url[1], 'geos': res})
        #     count = count + 1

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Start the load operations and mark each future with its URL
            future_to_url = {executor.submit(self.process_pollutants_data, url): url for url in pollutant_data}
            count = 0
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    data = future.result()
                    final_data.append({'site' : url[2], 'latitude' : url[0], 'longitude' : url[1], 'geos': data[url[2]]})
                except Exception as exc:
                    print('%r generated an exception: %s' % (url, exc))
                else:
                    print('%r page is %d bytes' % (url, len(data)))


        data = {
            "message" : "Location data response.",
            "status" : status.HTTP_200_OK,
            "data" : final_data,
        }
        return Response(data, status.HTTP_200_OK)
    
    # async def process_pollutants_data(self, data_res):
    def process_pollutants_data(self, data_res):
        res_data = []

        headers = {
            'Content-Type': 'application/json'
        }            

        geos_urls = [
            {
                "name" : "PM/GEOS-PM2p5",
                "standart_name" : "PM2p5",
                "url": "http://smog.spatialapps.net:8080/thredds/catalog/HKHAirQualityWatch/RecentAndArchive/PM/GEOS-PM2p5/catalog.xml",
                "order" : 1,
            },
            {
                "name" : "NO2/GEOS-NO2",
                "standart_name" : "NO2",
                "url": "http://smog.spatialapps.net:8080/thredds/catalog/HKHAirQualityWatch/RecentAndArchive/NO2/GEOS-NO2/catalog.xml",
                "order" : 2,
            },
            {
                "name" : "CO/GEOS-CO",
                "standart_name" : "CO",
                "url": "http://smog.spatialapps.net:8080/thredds/catalog/HKHAirQualityWatch/RecentAndArchive/CO/GEOS-CO/catalog.xml",
                "order" : 3,
            },
            {
                "name" : "O3/GEOS-O3",
                "standart_name" : "O3",
                "url": "http://smog.spatialapps.net:8080/thredds/catalog/HKHAirQualityWatch/RecentAndArchive/O3/GEOS-O3/catalog.xml",
                "order" : 4,
            },
            {
                "name" : "SO2/GEOS-SO2",
                "standart_name" : "SO2",
                "url":"http://smog.spatialapps.net:8080/thredds/catalog/HKHAirQualityWatch/RecentAndArchive/SO2/GEOS-SO2/catalog.xml",
                "order" : 5,
            },
        ]

        today = date.today()
        yesterday = today - timedelta(days = 7)
        today = today.strftime('%Y-%m-%d')
        
        res_data = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Start the load operations and mark each future with its URL
            future_to_url = {executor.submit(self.execute_url, geos, yesterday, today, headers, data_res): geos for geos in geos_urls}
            count = 0
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                # try:
                data = future.result()
                res_data.append(data)
                # except Exception as exc:
                #     print('%r generated an exception: %s' % (url, exc))
                # else:
                #     print('%r page is %d bytes' % (url, len(data)))
        # return res_data
    
        res_data.sort(key=lambda x: x.get('order'))
        for res in res_data:
            del res['order']
            del res['site']
        return {data_res[2] : res_data}
    

    def execute_url(self, geos, yesterday, today, headers, data_res):
        conn = http.client.HTTPConnection("smog.icimod.org")
        payload = json.dumps({
            "url": geos['url'],
            "data_ext": ".nc",
            "startDate": yesterday.strftime('%Y-%m-%d'),
            "endDate": today,
        })

        conn.request("POST", "/apps/airquality/slicedfromcatalog/", payload, headers)
        res = conn.getresponse()
        data = json.loads(res.read())

        if data['data']:
            # Second api calling.
            initial_data = f"HKHAirQualityWatch/RecentAndArchive/{geos['name']}/"
            data_dir = [f"{initial_data}{data['data'][-1]}"]

            payload = json.dumps({
                "DATADIR": data_dir,
                "LAYER": geos['standart_name'],
                "wkt": f"POINT({data_res[0]} {data_res[1]})",
                "type": "Point"
            })

            conn.request("POST", "/apps/airquality/timeseriesmodeldata/", payload, headers)
            timeseriesmodeldata_res = conn.getresponse()
            timeseriesmodeldata_data = json.loads(timeseriesmodeldata_res.read())

            data = timeseriesmodeldata_data['SeriesData'][0]if timeseriesmodeldata_data['SeriesData'] else [0.0, 0.0]
            if data:
                if data[0] == None:
                    data[0] = 0.0
                if data[1] == None:
                    data[1] = 0.0
            

            return {
                "name" : "PM2.5" if geos['standart_name'] == "PM2p5" else geos['standart_name'],
                "value" : data,
                "order" : geos['order'],
                "site" : data_res[2],
                }
        else:
            return {
                "name" : geos['standart_name'],
                "value" : [0,0],
                "order" : geos['order'],
                "site" : data_res[2],
                }


class GeosLocationSourceDataAPIView(APIView):
    model = LocationData

    def get(self, request, source):
        if source == 'air_now':
            source = self.model.SOURCE.AIR_NOW
        else:
            source = self.model.SOURCE.AERO_NET

        pollutant_data = self.model.objects.filter(source=source).values(
                'pollutant__name', 
                'source', 
                'site', 
                'latitude',
                'longitude',
                'pollutant__id',
                'saved_location',
                'StId',
                'enabled',
                'id'
            )
        
        res_dict = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Start the load operations and mark each future with its URL
            future_to_url = {executor.submit(self.process_pollutants_data, url): url for url in pollutant_data}
            count = 0
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    data = future.result()
                    res_dict[data['site']] = data['value']
                except Exception as exc:
                    print('%r generated an exception: %s' % (url, exc))
                else:
                    print('%r page is %d bytes' % (url, len(data)))
        
        for rec in pollutant_data:
            rec['id']  = rec['StId']
            rec['source'] = "AIR NOW" if rec['source'] == "AIRNOW" else "AERO NET"
            rec['geos'] = res_dict[rec['site']]
            rec['color'] = self.color_response(res_dict[rec['site']][1])
            
                 
        data = {
            "message" : "Location data response.",
            "status" : status.HTTP_200_OK,
            "data" : pollutant_data,
        }
        return Response(data, status.HTTP_200_OK)

    def color_response(self, value):
        if value >= 1 and value <= 50:
            return "00FF00"
        elif value >= 51 and value <= 100:
            return "FFFF00"
        elif value >= 101 and value <= 150:
            return "FFA500"
        elif value >= 151 and value <= 200:
            return "FF0000"
        elif value >= 201 and value <= 300:
            return "A020F0"
        elif value >= 301 and value <= 500:
            return "800000"
        else:
            return "FFFFFF"

    def process_pollutants_data(self, data_res):
        headers = {
            'Content-Type': 'application/json'
        }            
        pm_conn = http.client.HTTPConnection("smog.icimod.org")

        payload = json.dumps({
            "stId": data_res['StId'],
            "ModelClass": "UsEmbassyPm",
            "ModelClassDataList": "UsEmbassyDataList",
            "typeName": "pm",
            "StartDate": datetime.today().strftime('%Y-%m-%d'),
            "EndDate": f"{datetime.today().strftime('%Y-%m-%d')}-23-59"
        })

        pm_conn.request("POST", "/apps/airquality/getData/", payload, headers)
        res = pm_conn.getresponse()
        data = json.loads(res.read())

        return {
            "value" : data['SeriesData'][0] if data['SeriesData'] else [0,0],
            "site" : data_res['site']
        }