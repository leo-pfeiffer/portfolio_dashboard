import datetime


def date_range_gen(start_date: datetime.date, end_date: datetime.date):
    """
    Generator for all dates between start_date and end_date (inclusive).
    :param start_date: start date
    :param end_date: end date
    """
    for n in range(int((end_date - start_date).days + 1)):
        yield start_date + datetime.timedelta(n)
