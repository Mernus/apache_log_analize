# apache_log_analize
This is Django project for downloading, read and parse data from logfile.

## Download the Project

First, clone the repository to your local machine:

```bash
git clone git@github.com:Mernus/apache_log_analize.git.git
```

Install the requirements:

```bash
pip install -r requirements.txt
```

## Set up a database

There's a lot of different database software that can store data for your site. You can use the default one, `sqlite3`.

This is already set up in this part of your `mysite/settings.py` file:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
```

To create a database for our project, run the following in the console: `python manage.py migrate` (you need to be in directory that contains the `manage.py` file). If that goes well, you should see something like this:

```
(venv) C:\Users\mernu\PycharmProjects\apache_log_analize>python manage.py migrate
Operations to perform:
  Apply all migrations: auth, admin, contenttypes, sessions
Running migrations:
  Rendering model states... DONE
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying auth.0009_alter_user_last_name_max_length... OK
  Applying sessions.0001_initial... OK
```

## Run Project Locally

Finally, run the development server:

```bash
python manage.py runserver
```

The project will be available at **127.0.0.1:8000**.

Remember to run everything in the virtualenv. If you don't see a prefix `(myvenv)` in your console, you need to activate your virtualenv. Typing `myvenv\Scripts\activate` on Windows or
`source myvenv/bin/activate` on Mac OS X or Linux will do this for you.


## Adding data from logfile to database

To add data from logfile you need to copy url of logfile, go to project directory, enter to virtual env and run this command.
You need to paste your url instead of mine.

```
(venv) \apache_log_analize>python manage.py log_parse -lp http://www.almhuette-raith.at/apache-log/access.log
```

Then logfile data will be downloaded, read and parsed. And you can interact with logfile or it data in the web.


## Management command

File log_parse.py where defined command to add logfile you can find at this path:

```
\apache_log_analize\analizer\management\commands\log_parse.py
```

Command has one required arguments that contains path from which need to download, read and parse log.
Argument name is '--log_path', short name is '-lp'. Argument take string with url of log and has one help message.

```
    def add_arguments(self, parser):
        parser.add_argument('-lp', "--log_path", type=str,
                            required=True,
                            help='Download, parse and push to db data from log(print the url after log_parse)')
```

Custom command has static method for download log by urllog and progress bar for download, read and parse downloaded file. File parsed with regular expression, added to list and pushed to db when size of list = 999 to minimize requests to database.

```
 @staticmethod
    def read_parse_log(urllog, filename):
        pattern = r"([\d.]+) \S+ \S+ \[(\d{2}/[A-Za-z]+/\d{1,4}:\d{1,2}:\d{1,2}:\d{1,2}) (\+\d{4})\]" + \
                  r" \"(\S+) (.*?) (\S+)\" (\d+|-) (\d+|-) \"(.*?)\" \".*?\" \".*?\""
        batch_size = 999
        new_log = Logfile(log_url=urllog)
        new_log.save()
        object_batch = []
        req = requests.get(urllog, stream=True)
        total_size = int(req.headers.get('content-length', 0))
        created_file = open(filename, 'w')
        created_file.close()
        cutted_line = ""
        with open(filename, 'r+b') as file:
            for data in tqdm(req.iter_content(1024),
                             total=math.ceil(total_size // 1024),
                             unit='KB', unit_scale=True, desc="Download, read and parse log"):
                file.write(data)
                file.seek(-len(data), 1)
                for line in file.readlines():
                    line = line.decode('UTF-8')
                    if line[-1] != '\n':
                        cutted_line = line
                        break
                    line = cutted_line + line
                    cutted_line = ""
                    match = re.match(pattern, line)
                    if match is None:
                        continue
                    datetime_format = datetime.strptime(match.group(2) + " UTC" + match.group(3),
                                                        '%d/%b/%Y:%H:%M:%S %Z%z')
                    object_batch.append(Logdata(datetime=datetime_format, ip=match.group(1),
                                                http_method=match.group(4),
                                                requested_path=match.group(5), http_protocol=match.group(6),
                                                status_code=match.group(7), size_requested_obj=match.group(8),
                                                referer=match.group(9), logfile=new_log))
                    if len(object_batch) == batch_size:
                        Logdata.objects.bulk_create(object_batch)
                        object_batch = []
        if Logfile.objects.filter(log_url=urllog).latest('added_datetime').logdata_set.count() == 0:
            Logfile.objects.filter(log_url=urllog).latest('added_datetime').delete()
```


And method to process the situation when logfile with this url is in the database:

```
@staticmethod
    def interact_with_same_log_indb(self, urllog):
        logs_added = Logfile.objects.filter(log_url=urllog)
        if logs_added:
            self.stdout.write("\nThis log has been also add to database")
            self.stdout.write(
                "\nYou can remove already added or add this log without delete previous\n\nLogs with this url\n\n")
            for log_id, log in enumerate(logs_added):
                self.stdout.write(
                    str(log_id + 1) + ".  Added: " + log.added_datetime.strftime('%d %b %Y %H:%M:%S') + "\n")
            self.stdout.write(
                "Print the number from 1 to to pick log to delete\n")
            self.stdout.write(
                "'Add' to add without delete\n'Cancel' to cancel action\n\n")
            while True:
                answer = input("Answer: ")
                try:
                    if 0 < int(answer) <= logs_added.count():
                        logs_added[int(answer) - 1].delete()
                        self.stdout.write("Logfile has been successful delete\n\n")
                        break
                except ValueError:
                    if answer.lower() == "cancel":
                        raise Exception("\nYou answer 'cancel', log will not be added\n")
                    elif answer.lower() == "add":
                        self.stdout.write("New Log will be added without deleting previous\n\n")
                        break
                self.stdout.write("Incorrect answer, try one more time\n\n")
```

And handle that interact with this methods:

```
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
```

After usage log will be deleted.

## Contributing

I love contributions, so please feel free to fix bugs, improve things. Just send a pull request.
