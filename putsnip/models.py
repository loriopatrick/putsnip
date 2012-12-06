from django.db import models

class Snip (models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    code = models.TextField()
    lan = models.CharField(max_length=30)
    tags = models.CharField(max_length=255)
    name = models.CharField(max_length=50)
    datetime = models.DateTimeField(auto_now_add=True)
    views = models.IntegerField(default=0)
    points = models.IntegerField(default=0)

class Account (models.Model):
    id = models.AutoField(primary_key=True)
    usr = models.CharField(max_length=20, null=False, unique=True)
    email = models.CharField(max_length=255)
    pwd = models.CharField(max_length=32, null=False)
    datetime = models.DateTimeField(auto_now_add=True)
    points = models.IntegerField(default=0)

class Vote (models.Model):
    snip = models.IntegerField()
    usr = models.IntegerField()
    up = models.BooleanField()
    date = models.DateTimeField(auto_now_add=True)