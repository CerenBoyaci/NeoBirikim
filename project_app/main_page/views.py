from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse



def home(request):
    return HttpResponse('anasayfa')

def main_info(request):
    return HttpResponse('informations')

def details(request,bilgi):
    return HttpResponse(f"{bilgi} detay sayfası")

def getInfoByCategory(request,category):
    text=""

    if(category=="kategori1"):
        text="kategori 1 e ait bilgiler"

    elif(category=="kategori2"):
        text="kategori 2 ye ait bilgiler"
    else:
        text="yanlış kategori seçimi"

    return HttpResponse(text)

def getInfoByCategoryId(request,category_id):
    return HttpResponse(category_id)
