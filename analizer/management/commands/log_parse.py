from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm
import re
import uuid
import requests
import os
import math
from analizer.models import Logdata, Logfile
from datetime import datetime


class Command(BaseCommand):
    help = 'Interact with apache log'

    def add_arguments(self, parser):
        parser.add_argument('-lp', "--log_path", type=str,
                            required=True,
                            help='Download, parse and push to db data from log(print the url after log_parse)')

    def interact_with_same_log_indb(self, urllog):
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
    def read_parse_log(urllog, filename):
        pattern = r"([\d.]+) \S+ \S+ \[(\d{2}/[A-Za-z]+/\d{1,4}:\d{1,2}:\d{1,2}:\d{1,2}) (\+\d{4})\]" + \
                  r" \"(\S+) (.*?) (\S+)\" (\d+|-) (\d+|-) \"(.*?)\" \".*?\" \".*?\""
        batch_size = 999
        # Сохраняем данный лог в бд
        new_log = Logfile(log_url=urllog)
        new_log.save()
        # Осуществляем проход по файлу
        object_batch = []
        req = requests.get(urllog, stream=True)
        # Получаем размер файла
        total_size = int(req.headers.get('content-length', 0))
        # Создаем файл
        created_file = open(filename, 'w')
        created_file.close()
        cutted_line = ""
        # Подгружаем часть лога
        with open(filename, 'r+b') as file:
            for data in tqdm(req.iter_content(1024),
                             total=math.ceil(total_size // 1024),
                             unit='KB', unit_scale=True, desc="Download, read and parse log"):
                file.write(data)  # Пишем подгруженную часть в файл
                file.seek(-len(data), 1)  # Перемещаем итератор в файле перед этой частью
                for line in file.readlines():  # Читаем подгруженную часть
                    line = line.decode('UTF-8')
                    if line[-1] != '\n':  # Если строка была не польностью подгружена, то запоминаем прочитанную часть
                        cutted_line = line
                        break
                    line = cutted_line + line  # Собираем строку
                    cutted_line = ""
                    match = re.match(pattern, line)  # Проверяем строку на соответствие паттерну
                    if match is None:
                        continue
                    # Преобразуем объект Datetime к удобному формату
                    datetime_format = datetime.strptime(match.group(2) + " UTC" + match.group(3),
                                                        '%d/%b/%Y:%H:%M:%S %Z%z')
                    # Добавляем объект в список
                    # через группы объекта match
                    # (ip) \S+ \S+ [(дата):(время) (часовой пояс)] "(HTTP метод) (Путь запроса) (HTTP протокол)"
                    #  (код ответа) (размер ответа) "(Реферал)" ".*?" ".*?"
                    object_batch.append(Logdata(datetime=datetime_format, ip=match.group(1),
                                                http_method=match.group(4),
                                                requested_path=match.group(5), http_protocol=match.group(6),
                                                status_code=match.group(7), size_requested_obj=match.group(8),
                                                referer=match.group(9), logfile=new_log))
                    # Как только количество элементов в списке становится максимальным для одноразоввого добавления в бд
                    if len(object_batch) == batch_size:
                        Logdata.objects.bulk_create(object_batch)
                        object_batch = []
        # Если нет данных в логе, то чистим бд от лога
        if Logfile.objects.filter(log_url=urllog).latest('added_datetime').logdata_set.count() == 0:
            Logfile.objects.filter(log_url=urllog).latest('added_datetime').delete()

    def handle(self, *args, **options):
        if options['log_path']:  # Если был отправлен путь
            Command.interact_with_same_log_indb(self, options['log_path'])  # Если были добавлены логи с таким url
            filename = "log-%s.txt" % uuid.uuid4()
            try:
                Command.read_parse_log(options['log_path'], filename)  # Читаем и парсим лог
                self.stdout.write("\nLog file has been read and parse")
            except KeyboardInterrupt:  # Если обработка лога была отменена, то чистим лог из бд
                self.stdout.write("\nAction has been cancel by user")
                Logfile.objects.filter(log_url=options['log_path']).latest('added_datetime').delete()
            except (
                    requests.exceptions.MissingSchema, requests.exceptions.ConnectionError,
                    requests.exceptions.InvalidURL):
                # Если лог не может быть загружен, то выводим пояснение
                raise CommandError("Error with download log file with url: " + options['log_path'])
            if os.path.isfile(filename):
                os.remove(filename)
