import django_tables2 as tables
import itertools


class PortfolioTable(tables.Table):
    row_number = tables.Column(verbose_name="Row", empty_values=())
    Symbol = tables.Column(verbose_name="Symbol")
    Name = tables.Column(verbose_name="Name")
    Size = tables.Column(verbose_name="Size", order_by="size")
    Price = tables.Column(verbose_name="Price", order_by="price")
    Subtotal = tables.Column(verbose_name="Subtotal", order_by="subtotal")
    Allocation = tables.Column(verbose_name="Allocation", order_by="allocation")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.counter = itertools.count()

    def render_row_number(self):
        return "%d" % next(self.counter)

    def render_id(self, value):
        return "<%s>" % value
