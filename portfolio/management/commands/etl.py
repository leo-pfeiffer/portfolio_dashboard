from django.core.management.base import BaseCommand
from portfolio.lib.etl import Extraction, Transformation, Loading


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        extraction = Extraction()
        extraction.run()
        extraction_data = extraction.data

        transformation = Transformation(extraction_data)
        transformation.run()
        transformation_data = transformation.data

        loading = Loading(transformation_data)
        loading.run()

