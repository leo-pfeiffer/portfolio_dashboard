import os
import datetime
import numpy as np
from bokeh.plotting import figure, output_file
from bokeh.io import export_png
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.generic import TemplateView
from django_tables2 import RequestConfig
from weasyprint import HTML

from degiro.settings import IMAGES, PDFS, MAIL

from portfolio.lib.helpers import generate_overview, create_performance_time_series, measure_loop
from portfolio.lib.yahoodata import get_yahoo_data
from portfolio.tables import PortfolioTable


# todo this need some serious refactoring
class CreateReport(TemplateView):

    def get(self, request, *args, **kwargs):
        financial_data = get_yahoo_data(['DOCU'], start=datetime.date(2020, 1, 1), end=datetime.date(2020, 7, 11))
        # data = financial_data.to_frame().reset_index()
        # data.columns = ['date1', 'price1']
        # data.price1 = (data.price1.pct_change().fillna(0) + 1).cumprod()

        # timestamp = datetime.date.today()

        data, timestamp = create_performance_time_series()

        perf_series = data.price1
        perf_series.index = data.date1

        measure_data = measure_loop(perf_series)

        for key, value in measure_data.items():
            if key == 'sharpe':
                measure_data[key] = np.round(value, 2)
            else:
                measure_data[key] = '{:.2%}'.format(value)

        start_date = data.date1.iloc[0]
        today = datetime.date.today()

        p = figure(y_axis_type="linear", x_axis_type='datetime',
                   plot_height=400, plot_width=800)
        p.xaxis.axis_label = 'Datum'
        p.yaxis.axis_label = 'Wertentwicklung (indiziert)'

        p.line(data.date1, data.price1, line_color="#009fdf", line_width=3)
        p.toolbar.logo = None
        p.toolbar_location = None
        output_file("static/degiro/images/line_chart.html", title="Line Chart")
        file_path = os.path.join(IMAGES, 'performance_graph.png')
        export_png(p, filename=file_path)

        depot = generate_overview()

        # Rendered
        report_path = os.path.join(PDFS, 'report.pdf')

        context = {'depot': depot, 'today': today, 'start_date': start_date, 'timestamp': timestamp,
                   'measure_data': measure_data}
        html_template = render_to_string('portfolio/create-report.html', context)
        html_object = HTML(string=html_template, base_url=request.build_absolute_uri())
        html_object.write_pdf(report_path)

        # send mail
        # send_report(report_path=report_path)

        pdf_file = html_object.write_pdf()
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = 'filename="home_page.pdf"'

        return response
