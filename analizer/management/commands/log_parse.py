from django.core.management.base import BaseCommand, CommandError
import requests
import math
from tqdm import tqdm
import os
import re
from analizer.models import Logdata, Logfile
from datetime import datetime


class Command(BaseCommand):
    help = 'Interact with apache log'

    def add_arguments(self, parser):
        parser.add_argument('-lp', "--log_path", type=str,
                            required=True,
                            help='Download, parse and push to db data from log(print the url after log_parse)')

    @staticmethod
    def same_log_indb(self, urllog):
        # Получаем все логи с данным url
        logs_added = Logfile.objects.filter(log_url=urllog)
        if logs_added:
            self.stdout.write("\nThis log has been also add to database")
            self.stdout.write(
                "\nYou can remove already added or add this log without delete previous\n\nLogs with this url\n\n")
            # Выводим все полученные логи
            for log_id, log in enumerate(logs_added):
                self.stdout.write(
                    str(log_id + 1) + ".  Added: " + log.added_datetime.strftime('%d %b %Y %H:%M:%S') + "\n")
            self.stdout.write(
                "Print the number from 1 to to pick log to delete\n")
            self.stdout.write(
                "'Add' to add without delete\n'Cancel' to cancel action\n\n")
            while True:
                answer = input("Answer: ")  # Обработка ответа
                try:
                    if 0 < int(answer) <= logs_added.count():  # Если выбрана опция удаления лога,
                        logs_added[int(answer) - 1].delete()  # то удаляем лог под выбранным номером
                        self.stdout.write("Logfile has been successful delete\n\n")
                        break
                except ValueError:
                    if answer.lower() == "cancel":  # Если добавление отменено, то вызываем исключение с сообщением
                        raise Exception("\nYou answer 'cancel', log will not be added\n")
                    elif answer.lower() == "add":  # Если выбрана опция с добавлением без удаления,
                        self.stdout.write("New Log will be added without deleting previous\n\n")
                        break  # то выводим сообщение и выходим иц цикла
                self.stdout.write("Incorrect answer, try one more time\n\n")  # Если не прошла ни одна проверка,
                # то выполняем цикл дальше с выводом поясняющего сообщения

    @staticmethod
    def download_log(self, urllog):
        # Пытаемся получить доступ к логу по url
        req = requests.get(urllog, stream=True)
        # Получаем размер файла
        total_size = int(req.headers.get('content-length', 0))
        # Производим запись данных из лога в файл
        with open('log.txt', 'wb') as file:
            for data in tqdm(req.iter_content(1024), total=math.ceil(total_size // 1024), unit='KB',
                             unit_scale=True, desc='Downloading log file'):
                file.write(data)
        self.stdout.write("\nLog file has been downloaded")

    @staticmethod
    def read_parse_log(urllog):
        pattern = r"([\d.]+) \S+ \S+ \[(\d{2}/[A-Za-z]+/\d{1,4}:\d{1,2}:\d{1,2}:\d{1,2}) (\+\d{4})\]" + \
                  r" \"(\S+) (.*?) (\S+)\" (\d+|-) (\d+|-) \"(.*?)\" \".*?\" \".*?\""
        batch_size = 999
        # Сохраняем данный лог в бд
        new_log = Logfile(log_url=urllog)
        new_log.save()
        # Осуществляем проход по файлу
        with open('log.txt', 'r') as file:
            object_batch = []
            for line in tqdm(file.readlines(), desc='Reading and parsing log file', unit_scale=True):
                # Проверяем строку на соответствию паттерну
                result = re.match(pattern, line)
                if result is None:
                    continue
                # Преобразуем объект Datetime к удобному формату
                datetime_format = datetime.strptime(result.group(2) + " UTC" + result.group(3),
                                                    '%d/%b/%Y:%H:%M:%S %Z%z')
                # Добавляем объект в список
                # через группы объекта match
                # (ip) \S+ \S+ [(дата):(время) (часовой пояс)] "(HTTP метод) (Путь запроса) (HTTP протокол)"
                #  (код ответа) (размер ответа) "(Реферал)" ".*?" ".*?"
                object_batch.append(Logdata(datetime=datetime_format, ip=result.group(1),
                                            http_method=result.group(4),
                                            requested_path=result.group(5), http_protocol=result.group(6),
                                            status_code=result.group(7), size_requested_obj=result.group(8),
                                            referer=result.group(9), logfile=new_log))
                # Как только количество элементов в списке становится максимальным для одноразоввого добавления в бд
                if len(object_batch) == batch_size:
                    Logdata.objects.bulk_create(object_batch)
                    object_batch.clear()

    def handle(self, *args, **options):
        if options['log_path']:  # Если был отправлен путь
            Command.same_log_indb(self, options['log_path'])  # Если были добавлены логи с таким url
            try:
                Command.download_log(self, options['log_path'])  # Подгружаем данные из лога
                Command.read_parse_log(options['log_path'])  # Читаем и парсим лог
                self.stdout.write("\nLog file has been download, read and parse")
            except KeyboardInterrupt:  # Если обработка лога была отменена, то чистим лог из бд
                self.stdout.write("\nAction has been cancel by user")
                Logfile.objects.filter(log_url=options['log_path']).latest('added_datetime').delete()
            except (
                    requests.exceptions.MissingSchema, requests.exceptions.ConnectionError,
                    requests.exceptions.InvalidURL):
                # Если лог не может быть загружен, то выводим пояснение
                raise CommandError("Error with download log file with url: " + options['log_path'])
        # Если файл лога был загружен, то удаляем
        if os.path.isfile('log.txt'):
            os.remove('log.txt')
