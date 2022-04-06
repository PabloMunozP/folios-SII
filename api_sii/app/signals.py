import imp
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.db.models.signals import  post_save
from django.core.signals import request_started,request_finished

def user_login(sender, request)