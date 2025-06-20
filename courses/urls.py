from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('<int:pk>/', views.course_detail, name='course_detail'),
    path('<int:course_id>/enroll/', views.enroll_course, name='enroll'),
    path('confirm/<int:course_id>/', views.payment_confirm, name='payment_confirm'),
    path('cancel/', views.payment_cancel, name='payment_cancel'),

]



# from django.urls import path
# from . import views

# app_name = 'courses'

# urlpatterns = [
#     path('', views.course_list_view, name='course_list'),
#     path('my/', views.my_courses_view, name='my_courses'),
#     path('create/', views.create_course_view, name='create_course'),
#     path('checkout/', views.checkout, name='checkout'),
#     path('simple_checkout/', views.simple_checkout, name='simple_checkout'),
#     path('<slug:slug>/', views.course_detail_view, name='course_detail'),
#     path('courses/<int:course_id>/enroll/', views.course_enroll, name='course_enroll'),

# ]
