from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.course_list_view, name='course_list'),
    path('my/', views.my_courses_view, name='my_courses'),
    path('create/', views.create_course_view, name='create_course'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/<int:enrollment_id>/', views.checkout_with_id, name='checkout_with_id'),
    path('simple_checkout/', views.simple_checkout, name='simple_checkout'),
    path('<slug:slug>/', views.course_detail_view, name='course_detail'),
    path('courses/<int:course_id>/enroll/', views.course_enroll, name='course_enroll'),
    path('payment/success/<int:enrollment_id>/', views.payment_success_webhook, name='payment_success_webhook'),

]
