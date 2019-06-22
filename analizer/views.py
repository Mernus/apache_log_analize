from django.views import generic
from .models import Logfile, Logdata
from openpyxl import Workbook
from django.shortcuts import render
import warnings
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

warnings.simplefilter("ignore")


class IndexView(generic.ListView):
    template_name = 'analizer/index.html'
    paginate_by = 5

    def get_queryset(self):
        # Получаем все логи, если был применен поиск, то фильтруем
        object_list = Logfile.objects.all()
        query = self.request.GET.get("q")
        if query:
            object_list = object_list.filter(Q(log_url__icontains=query) |
                                             Q(added_datetime__year__icontains=query) |
                                             Q(added_datetime__month__icontains=query) |
                                             Q(added_datetime__day__icontains=query) |
                                             Q(added_datetime__hour__icontains=query) |
                                             Q(added_datetime__minute__icontains=query))
        self.queryset = object_list
        return object_list

    def get_context_data(self, **kwargs):
        # Получаем контекстные данные, добавляем данные из поиска
        context = super(IndexView, self).get_context_data(**kwargs)
        query = self.request.GET.get('q')
        if query:
            context['q'] = query
        return context


class LogDetailView(generic.ListView):
    paginate_by = 50
    template_name = 'analizer/logdetail.html'

    def get_queryset(self):
        # Получаем данные из нужного лога по pk, фильтруем если был применен поиск
        log = Logfile.objects.get(pk=self.kwargs.get('pk'))
        query = self.request.GET.get("q")
        object_list = get_obj_list(log, query)
        self.queryset = object_list
        return object_list

    def get_context_data(self, **kwargs):
        # Получаем контекстные данные, добавляем данные из поиска
        context = super(LogDetailView, self).get_context_data(**kwargs)
        query = self.request.GET.get('q')
        if query:
            context['q'] = query
        return context


class LogDataDetailView(generic.DetailView):
    model = Logdata
    template_name = 'analizer/logdatadetail.html'

    def get_context_data(self, **kwargs):
        # Получаем контекстные данные, добавляем данные из поиска
        context = super(LogDataDetailView, self).get_context_data(**kwargs)
        query = self.request.GET.get('q')
        if query:
            context['q'] = query
        return context


def get_obj_list(logfile, query):
    # Получаем все логи, если был применен поиск, то фильтруем
    object_list = logfile.logdata_set.all()
    if query:
        object_list = object_list.filter(Q(ip__icontains=query) |
                                         Q(datetime__year__icontains=query) |
                                         Q(datetime__month__icontains=query) |
                                         Q(datetime__day__icontains=query) |
                                         Q(datetime__hour__icontains=query) |
                                         Q(datetime__minute__icontains=query) |
                                         Q(http_method__icontains=query) |
                                         Q(requested_path__icontains=query) |
                                         Q(http_protocol__icontains=query) |
                                         Q(status_code__icontains=query) |
                                         Q(size_requested_obj__icontains=query) |
                                         Q(referer__icontains=query))
    return object_list


def collect_stats(request, pk_log):
    # Собираем необходимую статистику
    # Получаем данные из поиска, если они есть то фильтруем данные по логу, если нет то берем все данные из лога
    query = request.GET.get("q")
    logfile = get_object_or_404(Logfile, pk=pk_log)
    object_list = get_obj_list(logfile, query)
    ips = {}
    http_methods = {}
    sum_answer_size = 0
    # Проходим по данным лога и заполняем словари с ip и http методами
    # Заполняем в формате {'(метод или ip)': (количество использований)}
    # Находим сумму всех размеров ответа
    for log in object_list:
        string_ip = str(log.ip)
        if ips.get(string_ip) is not None:
            ips[string_ip] += 1
        else:
            ips[string_ip] = 1
        if http_methods.get(log.http_method) is not None:
            http_methods[log.http_method] += 1
        else:
            http_methods[log.http_method] = 1
        try:
            sum_answer_size += int(log.size_requested_obj)
        except ValueError:
            pass
    # Преобразуем полученные словари в списки кортежей
    # С сортировкой по количеству использований
    http_methods_list = sorted(http_methods.items(), key=lambda item: item[1], reverse=True)
    ips_list = sorted(ips.items(), key=lambda item: item[1], reverse=True)
    # Получаем количество уникальных ip
    unic_ips_count = len(ips_list)
    # Получаем первые 10 ip по популярности
    ten_first_ip_list = [ip for ip in ips_list if ips_list.index(ip) < 10]
    context = {'first_ips': ten_first_ip_list, 'http_methods': http_methods_list,
               'sum_answer_size': sum_answer_size, 'unic_ips_count': unic_ips_count}
    return render(request, "analizer/stats.html", context=context)


def xlsx_downloader(request, log_pk):
    # Загрузка данных из лога в формате xlsx
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    # Получаем лог, из которого нужны данные
    logfile = get_object_or_404(Logfile, pk=log_pk)
    response['Content-Disposition'] = 'attachment; filename={date}-logfile({log_url}).xlsx'.format(
        date=logfile.added_datetime.strftime('%d-%m-%Y/%H:%M'), log_url=logfile.log_url
    )
    # Получаем данные из поиска, если они есть то фильтруем данные по логу, если нет то берем все данные из лога
    query = request.GET.get("q")
    object_list = get_obj_list(logfile, query)
    # Формируем таблицу
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'Logfile Data'
    columns = ['Primary Key',
               'IP',
               'Date And Time',
               'HTTP Method',
               'Requested Path',
               'HTTP Protocol',
               'Status Code',
               'Response Size',
               'Referer', ]
    worksheet.append(columns)
    rows = object_list.values_list(
        'pk',
        'ip',
        'datetime',
        'http_method',
        'requested_path',
        'http_protocol',
        'status_code',
        'size_requested_obj',
        'referer'
    )
    for row in rows:
        worksheet.append(row)
    workbook.save(response)
    return response
# Create your views here.
