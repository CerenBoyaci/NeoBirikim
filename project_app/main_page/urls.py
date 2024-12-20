from django.urls import path
from.import views






urlpatterns = [
    path('',views.home),
    path('anasayfa',views.home),
    
    path('bilgiler listesi',views.main_info),
    path('<bilgi>',views.details),
    path('kategori/<int:category_id>',views.getInfoByCategoryId),
    path('kategori/<str:category>',views.getInfoByCategory),
]
