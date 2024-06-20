# custom_middleware.py
from django.template import TemplateDoesNotExist
from django.http import HttpResponseNotFound
import logging

logger = logging.getLogger(__name__)

class HandleTemplateDoesNotExistMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, TemplateDoesNotExist):
            logger.error(f"Template does not exist: {exception}")
           
            return HttpResponseNotFound("The requested template does not exist.")
        return None
