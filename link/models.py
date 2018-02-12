from django.db import models
from random import choice
from string import ascii_letters
from django.conf import settings


class Link(models.Model):
    """Модель ссылки"""

    name = models.CharField("Название", max_length=250, default="")
    source = models.URLField("Источник", max_length=250)
    link_hash = models.CharField("Хеш", max_length=250, unique=True, editable=False)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    refer_count = models.PositiveIntegerField("Количество переходов", default=0)

    def __str__(self):
        return (self.name or self.source) + "[" + self.link_hash + "]"

    def get_url(self):
        return settings.BASE_SITE_NAME + '/' + self.link_hash

    def update_counter(self):
        self.refer_count += 1
        self.save()

    def save(self, *args, **kwargs):
        if not self.id:
            self.link_hash = ''.join(choice(ascii_letters) for i in range(5))

        return super(Link, self).save(*args, **kwargs)