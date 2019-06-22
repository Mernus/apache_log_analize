from django.db import models


class Logfile(models.Model):
    log_url = models.URLField(verbose_name="Url of log file")
    added_datetime = models.DateTimeField(auto_now_add=True, verbose_name="Date and time when log added")


class Logdata(models.Model):
    datetime = models.DateTimeField(verbose_name="Date and time the request was received")
    ip = models.GenericIPAddressField(unpack_ipv4=True, verbose_name="IP address of client")
    http_method = models.CharField(max_length=300, verbose_name="Used HTTP method")
    requested_path = models.CharField(max_length=300, verbose_name="Requested resource path")
    http_protocol = models.CharField(max_length=9, verbose_name="HTTP protocol that the client used")
    status_code = models.PositiveSmallIntegerField(verbose_name="Status code send back by server")
    size_requested_obj = models.CharField(max_length=20, verbose_name="Size of the object requested")
    referer = models.CharField(max_length=500, verbose_name="URLs from which peoples are redirected to mine website")
    logfile = models.ForeignKey(Logfile, on_delete=models.CASCADE, verbose_name="Logfile from which data was added")

    def __iter__(self):
        for field in self._meta.local_fields:
            if field.name not in ["id", "logfile"]:
                value = getattr(self, field.name, None)
                yield (field.verbose_name, value)
