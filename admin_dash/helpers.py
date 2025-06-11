from io import BytesIO
from django.shortcuts import render
from django.http import HttpResponse
from xhtml2pdf import pisa
import os
# import xhtml2pdf.pisa as pisa
from django.template.loader import get_template

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()

    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None
