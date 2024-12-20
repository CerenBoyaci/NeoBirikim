from django.urls import path
from . import views




urlpatterns = [
    path('login/', views.user_login, name="user_login"),
    
    path('register', views.user_register, name="user_register"),
    path('logout', views.user_logout, name="user_logout"),
    path('home/', views.home, name="home"),
    path('about/', views.about, name="about"),
    path('communication/', views.communication, name="communication"),
    path('update_user/', views.update_user, name='update_user'),  
    path('add_consumption/', views.add_consumption, name='add_consumption'),
    path('success/', views.success_view, name='success'),
    path('add_income/', views.add_income, name='add_income'),
    path('financial_summary/', views.financial_summary, name='financial_summary'),
    path('compare/', views.compare, name='compare'),
    path('goals/', views.saving_goal_list, name='saving_goal_list'),
    path('goals/new/', views.create_saving_goal, name='create_saving_goal'),
    path('goals/<int:goal_id>/add/', views.add_saving, name='add_saving'),
    path('advice/', views.environmental_recommendations, name='environmental_recommendations'),
]

