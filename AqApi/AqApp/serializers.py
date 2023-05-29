from rest_framework import serializers
from AqApp.models import Site, Pollutant, PollutantProperty

class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ('station_id', 'site', 'station_type', 'longitude', 'latitude')

class PollutantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pollutant
        fields = ('pollutant_id', 'pollutant_name')

class PollutantPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = PollutantProperty
        fields = ('prop_id', 'color_id', 'aqi', 'value')
