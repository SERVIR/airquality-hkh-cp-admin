from django.contrib import admin
from .models import PolluantData, LocationData
# Register your models here.



class LocationDataModelSerailizer(admin.ModelAdmin):
    list_display = ['source', 'site', 'StId', 'enabled', 'saved_location', 'latitude', 'longitude']
    search_fields = ['source',]
    list_filter = ['enabled', 'source', 'saved_location']

admin.site.register(PolluantData)
admin.site.register(LocationData, LocationDataModelSerailizer)