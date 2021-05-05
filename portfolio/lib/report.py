from portfolio.lib.mail import Mail

# todo put report generation in here


class Report:

    def generate(self):
        pass

    def send(self):
        # todo include send_report here
        pass


def send_report(report_path: str, **kwargs):
    receiver_mail = kwargs.get('receiver_mail', 'leopold.pfeiffer@gmx.de')
    subject = kwargs.get('subject', 'Your DegiroAPI Report')
    body = kwargs.get('body', 'Hello,\n\nPlease find attached your current DegiroAPI portfolio report.\n\nKind regards,'
                              '\nLeopold\n\n')
    Mail.send(receiver_mail, subject, body, report_path)
