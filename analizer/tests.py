from django.test import TestCase
from analizer.models import Logfile
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
        self.assertQuerysetEqual(logfile, map(repr, response.context['object_list']))
        sizes_sum = 0
        ips = {}
        for logdata in first_log.logdata_set.all():
            try:
                sizes_sum += int(logdata.size_requested_obj)
            except ValueError:
                pass
            string_ip = str(logdata.ip)
            if ips.get(string_ip) is not None:
                ips[string_ip] += 1
            else:
                ips[string_ip] = 1
        ips_list = sorted(ips.items(), key=lambda item: item[1], reverse=True)
        ten_first_ip_list = [ip for ip in ips_list if ips_list.index(ip) < 10]
        sec_response = self.client.get("/stats/" + str(first_log.pk) + "/")
        self.assertEqual(sizes_sum, sec_response.context['sum_answer_size'])
        self.assertListEqual(list(ten_first_ip_list), list(sec_response.context['first_ips']))
