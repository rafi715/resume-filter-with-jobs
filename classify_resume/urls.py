from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('jobs/', views.jobs, name='jobs'),
    path('register/', views.register, name='register'),
    path('logout/', views.custom_logout, name='logout'),
    path('job-detail/<int:job_id>/', views.job_detail, name='job-detail'),

    path('admin-panel/', views.admins_panel, name='admin-panel'),
    path('admin-user-resume/<int:user_id>/', views.admin_view_user_profile, name='admin-user-resume'),
    path('admin-edit-job/<int:job_id>/', views.admin_edit_job, name='admin-edit-job'),
    path('admin-delete-job/<int:job_id>/', views.admin_delete_job, name='admin-delete-job'),
    path('admin-edit-email/<int:mail_id>/', views.admin_edit_email, name='admin-edit-email'),
    path('admin-delete-email/<int:mail_id>/', views.admin_delete_email, name='admin-delete-email'),
    path('admin-job-detail/<int:job_id>/', views.admins_job_details, name='admin-job-detail'),
    path('admin-remove-resume/<int:job_id>/<int:apply_id>/', views.admin_remove_applicant, name='admin-remove-resume'),
    path('admin-email-detail/', views.admin_email_details, name='admin-email-detail'),
    path('admin-add-job/', views.admin_add_job, name='admin-add-job'),
    path('admin-add-email/', views.admin_add_email, name='admin-add-email'),

    path('user-panel/', views.users_panel, name='user-panel'),
    path('user-jobs/', views.user_jobs, name='user-jobs'),
    path('user-resume/', views.get_user_resume, name='user-resume'),
    path('user-job-detail/<int:job_id>/', views.user_job_details, name='user-job-detail'),
    path('user-create-resume-personal/', views.user_create_resume_personal, name='user-create-resume-personal'),
    path(
        'user-create-resume-education/<int:education_id>/',
        views.user_create_resume_education,
        name='user-create-resume-education'
    ),
    path('user-create-resume-education/', views.user_create_resume_education, name='user-create-resume-edu'),
    path(
        'user-create-resume-professional/<int:profession_id>/',
        views.user_create_resume_professional,
        name='user-create-resume-professional'
    ),
    path('user-create-resume-professional/', views.user_create_resume_professional, name='user-create-resume-pro'),
    path(
        'user-create-resume-certificate/<int:certificate_id>/',
        views.user_create_resume_certificate,
        name='user-create-resume-certificate'
    ),
    path('user-create-resume-certificate/', views.user_create_resume_certificate, name='user-create-resume-certi'),
    path(
        'user-create-resume-skill/<int:skill_id>/',
        views.user_create_resume_skill,
        name='user-create-resume-skill'
    ),
    path('user-create-resume-skill/', views.user_create_resume_skill, name='user-create-resume-ski'),
    # path('user-create-resume/', views.user_create_resume, name='user-create-resume'),
    # path('user-create-resume/', views.user_create_resume, name='user-create-resume'),
    # path('user-create-resume/', views.user_create_resume, name='user-create-resume'),
    # path('user-create-resume/', views.user_create_resume, name='user-create-resume'),
    # path('user-change-password/', ChangePasswordView.as_view(), name='user-change-password'),
    path('user-change-password/', views.user_change_password, name='user-change-password'),

    # path('user-job-detail/<int:job_id>/', views.user_job_detail, name='doctor-view-appointment'),
    path('user-insert-education-detail/', views.user_insert_education_detail, name='user-insert-education-detail'),
    path('user-insert-work-detail/', views.user_insert_work_detail, name='user-insert-work-detail'),
    path('user-insert-skill-detail/', views.user_insert_skill_detail, name='user-insert-skill-detail'),
]
