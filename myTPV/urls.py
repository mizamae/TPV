"""
URL configuration for myTPV project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from debug_toolbar.toolbar import debug_toolbar_urls

from . import views

urlpatterns = [
    path("", views.home , name="home"),

    path("reports/", views.reports_home , name="MyTPV_reports_home"),
    path("sitesettings/", views.siteSettings , name="MyTPV_sitesettings"),

    #path("accounts/", include("django.contrib.auth.urls")),
    path('users/', include('UsersAPP.urls')),
    path("products/", include("ProductsAPP.urls")),
    path('admin/', admin.site.urls),
    path('django_plotly_dash/', include('django_plotly_dash.urls')),

    path("i18n/", include("django.conf.urls.i18n")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += debug_toolbar_urls()