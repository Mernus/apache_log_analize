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

To create a database for our blog, let's run the following in the console: `python manage.py migrate` (we need to be in directory that contains the `manage.py` file). If that goes well, you should see something like this:

```
(myvenv) ~/djangogirls$ python manage.py migrate
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
Create the database:

```bash
python manage.py migrate
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
(venv) C:\Users\mernu\PycharmProjects\apache_log_analize>python manage.py log_parse -lp http://www.almhuette-raith.at/apache-log/access.log
```

Then logfile data will be downloaded, read and parsed. And you can interact with logfile or it data in the web.

## Contributing

I love contributions, so please feel free to fix bugs, improve things. Just send a pull request.
