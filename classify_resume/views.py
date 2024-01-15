import math
import re
import bleach

from collections import Counter
from datetime import datetime

import html2text
from django.contrib import messages
from django.contrib.auth import login, get_user_model, logout
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import PasswordChangeView
from django.core.files.storage import FileSystemStorage
from django.forms import modelformset_factory
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy

from classify_resume.forms import BasicRegForm, LoginForm, JobForm, EmailForm, AppliedJobForm, JobEditForm, \
    CustomPasswordChangeForm, EmailEditForm, ApplicantPersonalInfoForm, ApplicantEducationInfoForm, \
    ApplicantProfessionalInfoForm, ApplicantCertificateInfoForm, ApplicantSkillInfoForm
from classify_resume.models import Jobs, ResumePersonalInfo, ResumeEducationInfo, ProfessionalExperienceInfo, SkillInfo, \
    AppliedJob, User, CertificateInfo, EmailContent


class EmailBackend(ModelBackend):
    def authenticate(self, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            return None
        else:
            if user.check_password(password):
                return user
        return None


def preprocess_text(text):
    return re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())


def calculate_cosine_similarity(text1, text2):
    text1 = preprocess_text(text1)
    text2 = preprocess_text(text2)

    words1 = Counter(text1.split())
    words2 = Counter(text2.split())

    intersection = set(words1.keys()) & set(words2.keys())

    dot_product = sum(words1[word] * words2[word] for word in intersection)
    magnitude1 = math.sqrt(sum(words1[word] ** 2 for word in words1.keys()))
    magnitude2 = math.sqrt(sum(words2[word] ** 2 for word in words2.keys()))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0

    return dot_product / (magnitude1 * magnitude2)


def ckeditor_clean(text):
    return html2text.html2text(text)


def index(request):
    context = {}
    return render(request, "index.html", context)


def jobs(request):
    context = {
        'jobs': Jobs.objects.filter(is_active=True)
    }
    return render(request, "jobs.html", context)


def custom_logout(request):
    logout(request)
    return redirect('index')


def register(request):
    context = {}
    signup_form = BasicRegForm()
    login_form = LoginForm()
    if request.method == 'POST' and 'register_user' in request.POST:
        signup_form = BasicRegForm(request.POST)
        if signup_form.is_valid():
            usr = signup_form.save(commit=False)
            password = usr.password
            usr.set_password(password)
            usr.save()
            messages.info(request, 'Please confirm your email address to complete the registration')
            return HttpResponseRedirect('/')
        else:
            messages.error(request, "ERROR! while saving info please retry again")

    if request.method == 'POST' and 'login_user' in request.POST:
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            username = login_form.cleaned_data.get('email')
            password = login_form.cleaned_data.get('password')
            user = EmailBackend.authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if user.is_superuser:
                    return HttpResponseRedirect('/admin-panel/')
                else:
                    return HttpResponseRedirect('/user-panel/')
            else:
                messages.error(request, 'Login credential not matched, please try valid credential.')
        else:
            messages.error(request, "Something went wrong please try again")

    context['sign_form'] = signup_form
    context['login_form'] = login_form
    return render(request, "signup.html", context)


def job_detail(request, job_id):
    context = {
        'current_job': Jobs.objects.get(id=job_id)
    }
    return render(request, "job-details.html", context)


def admin_required(view_func):
    @user_passes_test(lambda user: user.groups.filter(name='Admin').exists(), login_url='register', redirect_field_name=None)
    def wrapped_view(request, *args, **kwargs):
        if not request.user.groups.filter(name='Admin').exists():
            messages.error(request, 'You do not have permission to access this page.')
        return view_func(request, *args, **kwargs)
    return wrapped_view


@login_required(login_url='register')
# @admin_required
def admins_panel(request):
    context = {
        'jobs': Jobs.objects.filter(user=request.user)
    }
    return render(request, "admin-job-listing.html", context)


@login_required(login_url='register')
def admins_job_details(request, job_id):
    salary_counts = {}
    salary_ranges = [(0, 50000), (50001, 100000), (100001, 150000), (150001, 200000), (200001, 999999999)]
    jd = ckeditor_clean(Jobs.objects.get(id=job_id, is_active=True).job_description)
    applicants = AppliedJob.objects.filter(apply_job=job_id, is_deleted=False)
    for applied_user in applicants:
        resume_text = ''
        for office_text in applied_user.user.user_resume.first().user_professional_info.all():
            resume_text += office_text.official_description
        cleaned_job_text = ckeditor_clean(resume_text)
        applied_user.similarity_score = calculate_cosine_similarity(jd, cleaned_job_text)

    sorted_applicants = sorted(applicants, key=lambda x: x.similarity_score, reverse=True)

    if sorted_applicants:
        top_rated = sorted_applicants[0]
        top_rated.apply_status = 'Short Listed'
        top_rated.save()

    for salary_range in salary_ranges:
        lower_bound, upper_bound = salary_range
        count = applicants.filter(expected_salary__range=(lower_bound, upper_bound)).count()
        salary_counts[f"{lower_bound}-{upper_bound}"] = count

    labels = list(salary_counts.keys())
    counts = list(salary_counts.values())

    context = {
        'charts_label': labels,
        'charts_value': counts,
        'applicants': sorted(applicants, key=lambda x: x.similarity_score, reverse=True)
    }
    return render(request, "admin.html", context)


@login_required(login_url='register')
def admin_remove_applicant(request, job_id, apply_id):
    applicant_data = AppliedJob.objects.get(id=apply_id)
    applicant_data.is_deleted = True
    applicant_data.save()
    return HttpResponseRedirect(f'/admin-job-detail/{job_id}/')


@login_required(login_url='register')
def admin_view_user_profile(request, user_id):
    context = {
        'user_info': ResumePersonalInfo.objects.filter(user_id=user_id).first()
    }
    return render(request, "admin-user-resume.html", context)


@login_required(login_url='register')
def admin_add_job(request):
    context = {}
    add_job_form = JobForm()
    if request.method == 'POST':
        add_job_form = JobForm(request.POST, request.FILES)
        if add_job_form.is_valid():
            try:
                new_job = add_job_form.save(commit=False)
                new_job.user = request.user
                new_job.save()
                return redirect('admin-panel')
            except Exception as e:
                print(e)
    context['job_form'] = add_job_form
    return render(request, "admin-add-job.html", context)


@login_required(login_url='register')
def admin_edit_job(request, job_id):
    context = {}
    instance = get_object_or_404(Jobs, pk=job_id)
    edit_job_form = JobEditForm(instance=instance)
    if request.method == 'POST':
        edit_job_form = JobEditForm(request.POST, request.FILES, instance=instance)
        if edit_job_form.is_valid():
            try:
                edit_job_form.save()
                return redirect('admin-panel')
            except Exception as e:
                print(e)
    context['job_form'] = edit_job_form
    context['job_data'] = instance
    return render(request, "admin-edit-job.html", context)


@login_required(login_url='register')
def admin_delete_job(request, job_id):
    Jobs.objects.get(id=job_id).delete()
    return redirect('admin-panel')


@login_required(login_url='register')
def admin_edit_email(request, mail_id):
    context = {}
    instance = get_object_or_404(EmailContent, pk=mail_id)
    edit_email_form = EmailEditForm(instance=instance)
    if request.method == 'POST':
        edit_email_form = EmailEditForm(request.POST, instance=instance)
        if edit_email_form.is_valid():
            try:
                edit_email_form.save()
                return redirect('admin-email-detail')
            except Exception as e:
                print(e)
    context['email_form'] = edit_email_form
    context['email_data'] = instance
    return render(request, "admin-edit-email.html", context)


@login_required(login_url='register')
def admin_delete_email(request, mail_id):
    EmailContent.objects.get(id=mail_id).delete()
    return redirect('admin-email-detail')


@login_required(login_url='register')
def admin_email_details(request):
    context = {
        'emails': EmailContent.objects.all()
    }
    return render(request, "admin-email-listing.html", context)


@login_required(login_url='register')
def admin_add_email(request):
    context = {}
    add_email_form = EmailForm()
    if request.method == 'POST':
        add_email_form = EmailForm(request.POST)
        if add_email_form.is_valid():
            try:
                new_job = add_email_form.save(commit=False)
                new_job.user = request.user
                new_job.save()
                return redirect('admin-email-detail')
            except Exception as e:
                print(e)
    context['email_form'] = add_email_form
    return render(request, "admin-add-email.html", context)


@login_required(login_url='register')
def users_panel(request):
    context = {
        'applied_jobs': AppliedJob.objects.filter(user=request.user),
        'user_info': ResumePersonalInfo.objects.filter(user_id=request.user.id).first()
    }
    return render(request, "user-applied-jobs.html", context)


@login_required(login_url='register')
def user_jobs(request):
    context = {
        "jobs": Jobs.objects.filter(is_active=True),
        'user_info': ResumePersonalInfo.objects.filter(user_id=request.user.id).first()
    }
    return render(request, "user-jobs.html", context)


@login_required(login_url='register')
# class ChangePasswordView(PasswordChangeView):
#     template_name = 'user-change-password.html'
#     form_class = CustomPasswordChangeForm
#     success_url = reverse_lazy('logout')
def user_change_password(request):
    context = {}
    update_pass_form = CustomPasswordChangeForm(usr=request.user)
    if request.method == 'POST':
        update_pass_form = CustomPasswordChangeForm(request.POST, usr=request.user)
        if update_pass_form.is_valid():
            logged_in_user = User.objects.get(id=request.user.id)
            passwd = update_pass_form.cleaned_data.get('new_password')
            logged_in_user.set_password(passwd)
            logged_in_user.save()
            return redirect('logout')
    context['change_pass_form'] = update_pass_form
    context['user_info'] = ResumePersonalInfo.objects.filter(user_id=request.user.id).first()
    return render(request, "user-change-password.html", context)


@login_required(login_url='register')
def user_job_details(request, job_id):
    context = {}
    current_job = Jobs.objects.get(id=job_id)
    apply_form = AppliedJobForm()
    if request.method == 'POST':
        apply_form = AppliedJobForm(request.POST)
        if apply_form.is_valid():
            applied = apply_form.save(commit=False)
            applied.user = request.user
            applied.apply_job = current_job
            applied.apply_date = datetime.now()
            applied.save()
    context['current_job'] = current_job
    context['apply_form'] = apply_form
    context['user_info'] = ResumePersonalInfo.objects.filter(user_id=request.user.id).first()
    return render(request, "user-job-details.html", context)


@login_required(login_url='register')
def get_user_resume(request):
    context = {
        'user_info': ResumePersonalInfo.objects.filter(user_id=request.user.id).first()
    }
    return render(request, "user-resume.html", context)


@login_required(login_url='register')
def user_create_resume_personal(request):
    context = {}
    user1 = request.user
    personal_record_exist = ResumePersonalInfo.objects.filter(user=request.user).exists()
    # if personal_record_exist:
    #     instance = ResumePersonalInfo.objects.filter(user=request.user).first()
    #     user_info_form = ApplicantPersonalInfoForm(instance=instance)
    #     if request.method == 'POST':
    #         user_info_form = ApplicantPersonalInfoForm(request.POST, request.FILES, instance=instance)
    #         if user_info_form.is_valid():
    #             ui_form = user_info_form.save(commit=False)
    #             ui_form.user = request.user
    #             ui_form.save()
    # else:
    #     user_info_form = ApplicantPersonalInfoForm()
    #     if request.method == 'POST':
    #         user_info_form = ApplicantPersonalInfoForm(request.POST)
    #         if user_info_form.is_valid():
    #             ui_form = user_info_form.save(commit=False)
    #             ui_form.user = request.user
    #             ui_form.save()
    if personal_record_exist:
        instance = ResumePersonalInfo.objects.get(user=user1)
        user_info_form = ApplicantPersonalInfoForm(request.POST, request.FILES, instance=instance) \
            if request.method == 'POST' else ApplicantPersonalInfoForm(instance=instance)
    else:
        user_info_form = ApplicantPersonalInfoForm(request.POST) if request.method == 'POST' \
            else ApplicantPersonalInfoForm()

    if request.method == 'POST' and user_info_form.is_valid():
        ui_form = user_info_form.save(commit=False)
        ui_form.user = user1
        ui_form.save()

    context['is_exist_personal'] = personal_record_exist
    context['is_exist_educational'] = ResumeEducationInfo.objects.filter(user_info__user_id=request.user).exists()
    context['is_exist_professional'] = ProfessionalExperienceInfo.objects.filter(user_info__user_id=request.user).exists()
    context['is_exist_skills'] = SkillInfo.objects.filter(user_info__user_id=request.user).exists()
    context['is_exist_certi'] = CertificateInfo.objects.filter(user_info__user_id=request.user).exists()
    # context['personal_data'] = ResumePersonalInfo.objects.get(user=request.user)
    context['user_info_form'] = user_info_form
    context['user_info'] = ResumePersonalInfo.objects.filter(user_id=request.user.id).first()
    return render(request, "user-create-resume-personal.html", context)


@login_required(login_url='register')
def user_create_resume_education(request, education_id=None):
    context = {}
    education_instance = get_object_or_404(ResumeEducationInfo, pk=education_id) if education_id else None
    resume_educational_exist = ResumeEducationInfo.objects.filter(user_info__user_id=request.user).exists()
    if education_instance:
        education_formset = modelformset_factory(
            ResumeEducationInfo,
            form=ApplicantEducationInfoForm,
            extra=0,
            can_delete=True
        )
    else:
        education_formset = modelformset_factory(
            ResumeEducationInfo,
            form=ApplicantEducationInfoForm,
            extra=1,
            can_delete=True
        )
    if request.method == 'POST':
        formset_edu = education_formset(
            request.POST,
            request.FILES,
            queryset=ResumeEducationInfo.objects.filter(user_info__user_id=request.user),
            prefix='education',
            # instance=education_instance
        )
        if formset_edu.is_valid():
            for form in formset_edu:
                if form.cleaned_data.get('DELETE'):
                    if form.instance.pk:
                        form.instance.delete()
                else:
                    form.instance.user_info = ResumePersonalInfo.objects.filter(user=request.user).first()
                    form.save()
            return redirect('user-create-resume-edu')
    else:
        formset_edu = education_formset(
            queryset=ResumeEducationInfo.objects.filter(user_info__user_id=request.user),
            prefix='education'
        )

    context['is_exist_personal'] = ResumePersonalInfo.objects.filter(user=request.user).exists()
    context['is_exist_educational'] = resume_educational_exist
    context['is_exist_professional'] = ProfessionalExperienceInfo.objects.filter(user_info__user_id=request.user).exists()
    context['is_exist_skills'] = SkillInfo.objects.filter(user_info__user_id=request.user).exists()
    context['is_exist_certi'] = CertificateInfo.objects.filter(user_info__user_id=request.user).exists()
    context['education_instance'] = education_instance
    context['educa_info_form'] = formset_edu
    context['user_info'] = ResumePersonalInfo.objects.filter(user_id=request.user.id).first()
    return render(request, "user-create-resume-education.html", context)


@login_required(login_url='register')
def user_create_resume_professional(request, profession_id=None):
    context = {}
    professional_instance = get_object_or_404(ProfessionalExperienceInfo, pk=profession_id) if profession_id else None
    resume_professional_exist = ProfessionalExperienceInfo.objects.filter(user_info__user_id=request.user).exists()
    if professional_instance:
        professional_formset = modelformset_factory(
            ProfessionalExperienceInfo,
            form=ApplicantProfessionalInfoForm,
            extra=0,
            can_delete=True
        )
    else:
        professional_formset = modelformset_factory(
            ProfessionalExperienceInfo,
            form=ApplicantProfessionalInfoForm,
            extra=1,
            can_delete=True
        )
    if request.method == 'POST':
        formset_pro = professional_formset(
            request.POST,
            queryset=ProfessionalExperienceInfo.objects.filter(user_info__user_id=request.user),
            prefix='profession'
        )
        if formset_pro.is_valid():
            for form in formset_pro:
                if form.cleaned_data.get('DELETE'):
                    if form.instance.pk:
                        form.instance.delete()
                else:
                    form.instance.user_info = ResumePersonalInfo.objects.filter(user=request.user).first()
                    form.save()
            return redirect('user-create-resume-pro')
    else:
        formset_pro = professional_formset(
            queryset=ProfessionalExperienceInfo.objects.filter(user_info__user_id=request.user),
            prefix='profession'
        )

    context['is_exist_personal'] = ResumePersonalInfo.objects.filter(user=request.user).exists()
    context['is_exist_educational'] = ResumeEducationInfo.objects.filter(user_info__user_id=request.user).exists()
    context['is_exist_professional'] = resume_professional_exist
    context['is_exist_skills'] = SkillInfo.objects.filter(user_info__user_id=request.user).exists()
    context['is_exist_certi'] = CertificateInfo.objects.filter(user_info__user_id=request.user).exists()
    context['professional_instance'] = professional_instance
    context['pro_info_form'] = formset_pro
    context['user_info'] = ResumePersonalInfo.objects.filter(user_id=request.user.id).first()
    return render(request, "user-create-resume-professional.html", context)


@login_required(login_url='register')
def user_create_resume_certificate(request, certificate_id=None):
    context = {}
    certificate_instance = get_object_or_404(CertificateInfo, pk=certificate_id) if certificate_id else None
    resume_certificate_exist = CertificateInfo.objects.filter(user_info__user_id=request.user).exists()
    if certificate_instance:
        certificate_formset = modelformset_factory(
            CertificateInfo,
            form=ApplicantCertificateInfoForm,
            extra=0,
            can_delete=True
        )
    else:
        certificate_formset = modelformset_factory(
            CertificateInfo,
            form=ApplicantCertificateInfoForm,
            extra=1,
            can_delete=True
        )
    if request.method == 'POST':
        formset_certi = certificate_formset(
            request.POST,
            request.FILES,
            queryset=CertificateInfo.objects.filter(user_info__user_id=request.user),
            prefix='certifi'
        )
        if formset_certi.is_valid():
            for form in formset_certi:
                if form.cleaned_data.get('DELETE'):
                    if form.instance.pk:
                        form.instance.delete()
                else:
                    form.instance.user_info = ResumePersonalInfo.objects.filter(user=request.user).first()
                    form.save()
            return redirect('user-create-resume-certi')
    else:
        formset_certi = certificate_formset(
            queryset=CertificateInfo.objects.filter(user_info__user_id=request.user),
            prefix='certifi'
        )

    context['is_exist_personal'] = ResumePersonalInfo.objects.filter(user=request.user).exists()
    context['is_exist_educational'] = ResumeEducationInfo.objects.filter(user_info__user_id=request.user).exists()
    context['is_exist_professional'] = ProfessionalExperienceInfo.objects.filter(user_info__user_id=request.user).exists()
    context['is_exist_skills'] = SkillInfo.objects.filter(user_info__user_id=request.user).exists()
    context['is_exist_certi'] = certificate_formset
    context['certificate_instance'] = certificate_instance
    context['certi_info_form'] = formset_certi
    context['user_info'] = ResumePersonalInfo.objects.filter(user_id=request.user.id).first()
    return render(request, "user-create-resume-certificate.html", context)


@login_required(login_url='register')
def user_create_resume_skill(request, skill_id=None):
    context = {}
    skill_instance = get_object_or_404(SkillInfo, pk=skill_id) if skill_id else None
    resume_skill_exist = SkillInfo.objects.filter(user_info__user_id=request.user).exists()
    skill_formset = modelformset_factory(
        SkillInfo,
        form=ApplicantSkillInfoForm,
        extra=0 if resume_skill_exist else 1,
        # can_delete=True
    )
    if request.method == 'POST':
        formset_skill = skill_formset(
            request.POST,
            queryset=SkillInfo.objects.filter(user_info__user_id=request.user),
            prefix='skil'
        )
        if formset_skill.is_valid():
            instances = formset_skill.save(commit=False)
            for form in instances:
                form.user_info = ResumePersonalInfo.objects.filter(user=request.user).first()
                form.save()
            # for form in formset_skill.deleted_forms:
            #     if form.instance.pk:
            #         form.instance.delete()
            return redirect('user-create-resume-ski')
    else:
        formset_skill = skill_formset(
            queryset=SkillInfo.objects.filter(user_info__user_id=request.user),
            prefix='skil'
        )

    context['is_exist_personal'] = ResumePersonalInfo.objects.filter(user=request.user).exists()
    context['is_exist_educational'] = ResumeEducationInfo.objects.filter(user_info__user_id=request.user).exists()
    context['is_exist_professional'] = ProfessionalExperienceInfo.objects.filter(user_info__user_id=request.user).exists()
    context['is_exist_skills'] = resume_skill_exist
    context['is_exist_certi'] = CertificateInfo.objects.filter(user_info__user_id=request.user).exists()
    context['skill_instance'] = skill_instance
    context['skill_info_form'] = formset_skill
    context['user_info'] = ResumePersonalInfo.objects.filter(user_id=request.user.id).first()
    return render(request, "user-create-resume-skill.html", context)


@login_required(login_url='register')
def user_create_resume_professional(request, profession_id=None):
    context = {}
    professional_instance = get_object_or_404(ProfessionalExperienceInfo, pk=profession_id) if profession_id else None
    resume_professional_exist = ProfessionalExperienceInfo.objects.filter(user_info__user_id=request.user).exists()
    if professional_instance:
        professional_formset = modelformset_factory(
            ProfessionalExperienceInfo,
            form=ApplicantProfessionalInfoForm,
            extra=0,
            can_delete=True
        )
    else:
        professional_formset = modelformset_factory(
            ProfessionalExperienceInfo,
            form=ApplicantProfessionalInfoForm,
            extra=1,
            can_delete=True
        )
    if request.method == 'POST':
        formset_pro = professional_formset(
            request.POST,
            queryset=ProfessionalExperienceInfo.objects.filter(user_info__user_id=request.user),
            prefix='profession'
        )
        if formset_pro.is_valid():
            for form in formset_pro:
                if form.cleaned_data.get('DELETE'):
                    if form.instance.pk:
                        form.instance.delete()
                else:
                    form.instance.user_info = ResumePersonalInfo.objects.filter(user=request.user).first()
                    form.save()
            return redirect('user-create-resume-pro')
    else:
        formset_pro = professional_formset(
            queryset=ProfessionalExperienceInfo.objects.filter(user_info__user_id=request.user),
            prefix='profession'
        )

    context['is_exist_personal'] = ResumePersonalInfo.objects.filter(user=request.user).exists()
    context['is_exist_educational'] = ResumeEducationInfo.objects.filter(user_info__user_id=request.user).exists()
    context['is_exist_professional'] = resume_professional_exist
    context['is_exist_skills'] = SkillInfo.objects.filter(user_info__user_id=request.user).exists()
    context['is_exist_certi'] = CertificateInfo.objects.filter(user_info__user_id=request.user).exists()
    context['professional_instance'] = professional_instance
    context['pro_info_form'] = formset_pro
    context['user_info'] = ResumePersonalInfo.objects.filter(user_id=request.user.id).first()
    return render(request, "user-create-resume-professional.html", context)


def user_insert_education_detail(request):
    if request.method == "POST":
        iterations_num = int((len(request.POST) - 1) / 4)
        get_user_info_fetch = ResumePersonalInfo.objects.get(user=request.user)
        for iter_no in range(iterations_num):
            new_education = ResumeEducationInfo.objects.create(
                user_info=get_user_info_fetch,
                degree_category=request.POST.get(f'degreeTitle_{iter_no}'),
                start_degree=request.POST.get(f'degreeStart_{iter_no}'),
                end_degree=request.POST.get(f'degreeEnd_{iter_no}'),
                degree_description=request.POST.get(f'degree_description_{iter_no}')
            )
            if request.FILES.get(f'degreeCertificate_{iter_no}'):
                new_education.degree_image = request.FILES[f'degreeCertificate_{iter_no}']
                new_education.save()
        return JsonResponse({'success': True})


def user_insert_work_detail(request):
    if request.method == "POST":
        iterations_num = int((len(request.POST) - 1) / 4)
        get_user_info_fetch = ResumePersonalInfo.objects.get(user=request.user)
        for iter_no in range(iterations_num):
            new_experience = ProfessionalExperienceInfo.objects.create(
                user_info=get_user_info_fetch,
                company_name=request.POST.get(f'companyTitle_{iter_no}'),
                job_title=request.POST.get(f'jobTitle_{iter_no}'),
                start_experience=request.POST.get(f'jobStart_{iter_no}'),
                end_experience=request.POST.get(f'jobEnd_{iter_no}'),
                official_description=request.POST.get(f'job_description_{iter_no}')
            )
        return JsonResponse({'success': True})


def user_insert_skill_detail(request):
    if request.method == "POST":
        iterations_num = int((len(request.POST) - 1) / 2)
        get_user_info_fetch = ResumePersonalInfo.objects.get(user=request.user)
        for iter_no in range(iterations_num):
            new_skill = SkillInfo.objects.create(
                user_info=get_user_info_fetch,
                skill_type=request.POST.get(f'skillTitle_{iter_no}'),
                skill_value=request.POST.get(f'skillPercentage_{iter_no}')
            )
        return JsonResponse({'success': True})
