import datetime
from django.contrib.auth import logout
from .models import SiteSettings

class SettingsInjectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.
        

    def process_request(self, request):
        pass

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        
        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
    
    def process_template_response(self, request, response):
        response.context_data["siteSettings"] = SiteSettings.load()
        return response
    
class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        settings = SiteSettings.load()
        if settings.SEC2LOGOUT > 0:
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            last_activity = request.session.get('last_activity', None)
            if last_activity:
                last_activity = datetime.datetime.strptime(last_activity, '%Y-%m-%d %H:%M:%S')
                if (datetime.datetime.now() - last_activity).seconds > settings.SEC2LOGOUT: # timeout duration
                    logout(request)
            if request.path != '/ping/': # to avoid updating last_activity with ping requests
                request.session['last_activity'] = current_time
        response = self.get_response(request)
        return response