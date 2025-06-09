from django.contrib import admin
from accounts.models import CustomUser, Shop
# Register your models here.
admin.site.register([
    # Import your models here
    CustomUser, Shop

])
