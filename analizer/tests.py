from django.test import TestCase
from analizer.models import Logfile, Logdata
from django.db.models import Q
from django.core import management


class ModelTest(TestCase):

    def setUp(self) -> None:
        management.call_command('log_parse', '-lp', "http://www.almhuette-raith.at/apache-log/access.log")

    def test_mod(self):
        logfile = Logfile.objects.filter(Q(log_url__icontains='3') |
                                         Q(added_datetime__year__icontains='3') |
                                         Q(added_datetime__month__icontains='3') |
                                         Q(added_datetime__day__icontains='3') |
                                         Q(added_datetime__hour__icontains='3') |
                                         Q(added_datetime__minute__icontains='3'))
        response = self.client.get("/", {'q': 3})
        first_log = Logfile.objects.first()
        sec_response = self.client.get("/" + str(first_log.pk) + "/", {'q': 132})
        filtred_log = first_log.logdata_set.filter(Q(ip__icontains='132') |
                                                   Q(datetime__year__icontains='132') |
                                                   Q(datetime__month__icontains='132') |
                                                   Q(datetime__day__icontains='132') |
                                                   Q(datetime__hour__icontains='132') |
                                                   Q(datetime__minute__icontains='132') |
                                                   Q(http_method__icontains='132') |
                                                   Q(requested_path__icontains='132') |
                                                   Q(http_protocol__icontains='132') |
                                                   Q(status_code__icontains='132') |
                                                   Q(size_requested_obj__icontains='132') |
                                                   Q(referer__icontains='132'))
        self.assertQuerysetEqual(logfile, map(repr, response.context['object_list']))
        self.assertQuerysetEqual(filtred_log, map(repr, sec_response.context['object_list']))
