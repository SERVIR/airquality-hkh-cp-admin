from django.db import models
# from django.contrib.gis.db import models as gis_models
# from django.contrib.gis.geos import Point

# Create your models here.

STATION_TYPE_CHOICES = (
    ("1", "GROUND"),("2", "STATION"), ("3", "BKK")
)

class Site(models.Model):
    station_id = models.IntegerField(primary_key=True)
    site = models.CharField(max_length=200)
    station_type = models.CharField(STATION_TYPE_CHOICES, max_length=50)
    longitude = models.FloatField()
    latitude = models.FloatField()
    
    def __str__(self):
        return f"{self.site}, {self.station_type}, {self.latitude}, {self.longitude}"

class Pollutant(models.Model):
    pollutant_id = models.AutoField(primary_key=True)
    pollutant_name = models.CharField(max_length=200)

class PollutantProperty(models.Model):
    prop_id = models.AutoField(primary_key=True)
    color_id = models.IntegerField()
    aqi = models.IntegerField()
    value = models.IntegerField()


# New model.
class PolluantData(models.Model):
    name = models.CharField(max_length=256, unique=True)
    enabled = models.BooleanField(default=True) 

    class Meta:
        verbose_name = "Pollutant"
    
    def __str__(self):
        return f"{self.name}"

# from django.contrib.gis.db import models
# from django.db.models import Manager as GeoManager

class LocationData(models.Model):
    class SOURCE:
        AIR_NOW = "AIRNOW"
        AERO_NET = "AERONET"

    SOURCE_CHOICES = (
        (SOURCE.AIR_NOW, SOURCE.AIR_NOW),
        (SOURCE.AERO_NET, SOURCE.AERO_NET),
    )

    pollutant = models.ForeignKey(PolluantData, on_delete=models.SET_NULL, null=True, blank=True)
    source = models.CharField(max_length=26, choices=SOURCE_CHOICES, default=SOURCE.AIR_NOW)
    site = models.CharField(max_length=256)
    latitude = models.FloatField(null=True, blank=True, default=0)
    longitude = models.FloatField(null=True, blank=True, default=0)
    # min_aqi = models.FloatField(null=True, blank=True, default=0)
    # max_aqi = models.FloatField(null=True, blank=True, default=0)
    enabled = models.BooleanField(default=True)
    StId = models.IntegerField(null=True, blank=True)
    saved_location = models.BooleanField(default=True)
    # location = models.PointField()
    # location = models.PointField(geography=True, default=Point(0.0, 0.0))
    # objects = GeoManager()

    class Meta:
        verbose_name = "Location"
    
    def __str__(self):
        return f"{self.site}"

    # def save(self, *args, **kwargs):
    #     if self.latitude and self.longitude:
    #         self.location = Point(self.latitude, self.longitude)
    #     super(LocationData, self).save(*args, **kwargs)
