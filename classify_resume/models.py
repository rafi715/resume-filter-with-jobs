from datetime import datetime

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(max_length=254, unique=True)
    is_completed = models.BooleanField('complete status', default=False)


class Jobs(models.Model):
    user = models.ForeignKey(User, related_name='user_jobs', on_delete=models.CASCADE)
    job_title = models.CharField(max_length=256, blank=True)
    total_position = models.IntegerField(blank=True, default=0)
    last_date = models.DateField(blank=True, null=True)
    ads = models.ImageField(upload_to='media/job/', default='media/job/default-ads.jpg')
    job_description = models.TextField(max_length=1000, blank=True)
    is_active = models.BooleanField(default=True)


class AppliedJob(models.Model):
    user = models.ForeignKey(User, related_name='user_applied', on_delete=models.CASCADE)
    apply_job = models.ForeignKey(Jobs, related_name='user_apply_job', on_delete=models.CASCADE)
    current_salary = models.IntegerField(blank=True, default=0)
    expected_salary = models.IntegerField(blank=True, default=0)
    apply_date = models.DateField(blank=True, null=True, default=datetime.now())
    apply_status = models.CharField(max_length=256, blank=True)
    is_deleted = models.BooleanField(default=False)


class EmailContent(models.Model):
    user = models.ForeignKey(User, related_name='user_emails', on_delete=models.CASCADE)
    email_title = models.CharField(max_length=256, blank=True)
    email_description = models.TextField(max_length=1000, blank=True)
    is_active = models.BooleanField(default=True)


class ResumePersonalInfo(models.Model):
    user = models.ForeignKey(User, related_name='user_resume', on_delete=models.CASCADE)
    user_full_name = models.CharField(max_length=256, blank=True)
    user_email = models.CharField(max_length=256, blank=True)
    user_dob = models.DateField(blank=True, null=True)
    user_contact_no = models.CharField(max_length=256, blank=True)
    user_degree = models.CharField(max_length=256, blank=True)
    user_portfolio = models.CharField(max_length=256, blank=True)
    user_tag_line = models.CharField(max_length=256, blank=True)
    user_experience = models.CharField(max_length=256, blank=True)
    user_image = models.ImageField(upload_to='media/profile/', default='media/profile/default-info.jpg')
    user_facebook = models.CharField(max_length=256, blank=True)
    user_linkedin = models.CharField(max_length=256, blank=True)
    user_skype = models.CharField(max_length=256, blank=True)
    user_twitter = models.CharField(max_length=256, blank=True)
    user_instagram = models.CharField(max_length=256, blank=True)
    user_address = models.CharField(max_length=256, blank=True)
    about_description = models.TextField(max_length=1000, blank=True)


class ResumeEducationInfo(models.Model):
    user_info = models.ForeignKey(ResumePersonalInfo, related_name='user_education_info', on_delete=models.CASCADE)
    degree_category = models.CharField(max_length=256, blank=True)
    start_degree = models.DateField(blank=True, null=True)
    end_degree = models.DateField(blank=True, null=True)
    degree_image = models.ImageField(upload_to='media/degree/', default='media/degree/default-degree.jpg')
    degree_description = models.TextField(max_length=1000, blank=True)


class ProfessionalExperienceInfo(models.Model):
    user_info = models.ForeignKey(ResumePersonalInfo, related_name='user_professional_info', on_delete=models.CASCADE)
    company_name = models.CharField(max_length=256, blank=True)
    job_title = models.CharField(max_length=256, blank=True)
    start_experience = models.DateField(blank=True, null=True)
    end_experience = models.DateField(blank=True, null=True)
    official_description = models.TextField(max_length=1000, blank=True)


class SkillInfo(models.Model):
    user_info = models.ForeignKey(ResumePersonalInfo, related_name='user_skill_info', on_delete=models.CASCADE)
    skill_type = models.CharField(max_length=256, blank=True)
    skill_value = models.CharField(max_length=256, blank=True)


class CertificateInfo(models.Model):
    user_info = models.ForeignKey(ResumePersonalInfo, related_name='user_cert_info', on_delete=models.CASCADE)
    cert_title = models.CharField(max_length=500, blank=True)
    cert_image = models.ImageField(upload_to='media/certificate/', default='media/certificate/default-certificate.jpg')
    cert_description = models.TextField(max_length=1000, blank=True)

