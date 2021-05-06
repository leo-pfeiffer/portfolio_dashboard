import datetime
import os

import pandas as pd
from weasyprint import HTML

from portfolio.lib.performance_measures import PerformanceMeasures
from portfolio.lib.aggregation import create_performance_series, create_portfolio
from portfolio.lib.mail import Mail

from bokeh.plotting import figure, output_file
from project.settings import IMAGES, PDFS
from bokeh.io import export_png
from django.template.loader import render_to_string


class Report:

    def __init__(self):
        self.performance_series = pd.Series
        self.measure_data = dict()
        self.depot = list()

    def generate(self, base_url):

        self._prepare_data()

        p = figure(y_axis_type="linear", x_axis_type='datetime',
                   plot_height=400, plot_width=800)

        p.xaxis.axis_label = 'Datum'
        p.yaxis.axis_label = 'Wertentwicklung (indiziert)'

        p.line(self.performance_series.index.to_list(), self.performance_series.to_list(),
               line_color="#009fdf", line_width=3)
        p.toolbar.logo = None
        p.toolbar_location = None

        output_path = os.path.join(IMAGES, 'line_chart.html')
        output_file(output_path, title="Line Chart")

        file_path = os.path.join(IMAGES, 'performance_graph.png')
        export_png(p, filename=file_path)

        # Rendered
        report_path = os.path.join(PDFS, 'report.pdf')

        context = {'depot': self.depot,
                   'measure_data': self.measure_data}

        html_template = render_to_string('portfolio/create-report.html', context)
        html_object = HTML(string=html_template, base_url=base_url)
        html_object.write_pdf(report_path)

        pdf_file = html_object.write_pdf()
        return pdf_file

    def _prepare_data(self):
        self.performance_series = create_performance_series()

        self.measure_data = PerformanceMeasures.measure_loop(self.performance_series)

        for key, value in self.measure_data.items():
            if key == 'sharpe':
                self.measure_data[key] = round(value, 2)
            else:
                self.measure_data[key] = '{:.2%}'.format(value)

        portfolio = create_portfolio()
        self.depot = portfolio.to_dict('records')

    def send(self):
        # todo include send_report here
        pass


def send_report(report_path: str, **kwargs):
    receiver_mail = kwargs.get('receiver_mail', 'leopold.pfeiffer@gmx.de')
    subject = kwargs.get('subject', 'Your DegiroAPI Report')
    body = kwargs.get('body', 'Hello,\n\nPlease find attached your current DegiroAPI portfolio report.\n\nKind regards,'
                              '\nLeopold\n\n')
    Mail.send(receiver_mail, subject, body, report_path)
