from django.http import HttpResponse
import os
from xhtml2pdf import pisa
# import xhtml2pdf.pisa as pisa
from django.template.loader import get_template
from django.conf import settings

def render_to_pdf(template_path, context_dict):
    template = get_template(template_path)
    html = template.render(context_dict)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="invoice.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=fetch_resources)

    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

def fetch_resources(uri, rel):
    """
    Callback to allow xhtml2pdf to fetch additional resources such as stylesheets.
    """
    if settings.DEBUG:
        return uri
    else:
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
        return path