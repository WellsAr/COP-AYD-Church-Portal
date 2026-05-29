from django.urls import path

from .views import (
    dashboard,
    logout_view,
    mark_attendance,
    member_detail,
    member_list,
    register_member,
    attendance_report,
    attendance_report_pdf,
)

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('logout/', logout_view, name='logout'),
    path('members/', member_list, name='member_list'),
    path('member/<int:member_id>/', member_detail, name='member_detail'),
    path('register/', register_member, name='register_member'),
    path('attendance/', mark_attendance, name='mark_attendance'),
    path('reports/', attendance_report, name='attendance_report'),
    path('reports/pdf/', attendance_report_pdf, name='attendance_report_pdf'),
]