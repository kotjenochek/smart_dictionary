from django.db import models


class User(models.Model):
    name = models.CharField('User name', max_length=50)
    xp = models.IntegerField(default=0)
    image = models.ImageField(null=True, blank=True)


class Learnword(models.Model):
    User = models.ForeignKey(User, on_delete=models.CASCADE)
    german_word = models.CharField('german word', max_length=50)
    russian_word = models.CharField('russian word', max_length=50)
    image = models.ImageField(null=True, blank=True)
    german_pronunciation = models.FileField(null=True, blank=True, upload_to='Audio/de/')
    russian_pronunciation = models.FileField(null=True, blank=True, upload_to='Audio/ru/')


class UnsavedLearnword(models.Model):
    User = models.ForeignKey(User, on_delete=models.CASCADE)
    german_word = models.CharField('german word', max_length=50)
    russian_word = models.CharField('russian word', max_length=50)
    image = models.ImageField(null=True, blank=True)


class Training(models.Model):
    User = models.ForeignKey(User, on_delete=models.CASCADE)
    german_word = models.CharField('german word', max_length=50)
    russian_word = models.CharField('russian word', max_length=50)
    german_pronunciation = models.FileField(null=True, blank=True, upload_to='Audio/de/')
    russian_pronunciation = models.FileField(null=True, blank=True, upload_to='Audio/ru/')
    image = models.ImageField(null=True, blank=True)
    learnword_id = models.IntegerField()
    counter = models.IntegerField()

class Picture(models.Model):
    image = models.ImageField(null=True, blank=True)
