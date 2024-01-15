import os

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError

from classify_resume.models import User, Jobs, AppliedJob, EmailContent, ResumePersonalInfo, ResumeEducationInfo, \
    ProfessionalExperienceInfo, SkillInfo, CertificateInfo


def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.jpg', '.png', '.jpeg']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension.')


class BasicRegForm(forms.ModelForm):
    username = forms.CharField(
        min_length=4, max_length=15,
        widget=forms.TextInput(attrs={'placeholder': 'User Name'})
    )
    first_name = forms.CharField(
        min_length=3, max_length=15,
        widget=forms.TextInput(attrs={'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        min_length=3, max_length=15,
        widget=forms.TextInput(attrs={'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        min_length=6, max_length=40,
        widget=forms.TextInput(attrs={'placeholder': 'Email Address'})
    )
    password = forms.CharField(
        min_length=6, max_length=20,
        widget=forms.PasswordInput(render_value=False, attrs={'placeholder': 'Password'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Repeat Password'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password')

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists")
        return email

    def clean_password(self):
        password = self.cleaned_data['password']
        confirm_password = self.data['confirm_password']
        if password != confirm_password:
            raise forms.ValidationError("password does not matched")
        return password


class CustomPasswordChangeForm(forms.Form):
    old_password = forms.CharField(
        min_length=6, max_length=20,
        widget=forms.PasswordInput(render_value=False, attrs={'placeholder': 'Password'}),
        label='Old Password'
    )
    new_password = forms.CharField(
        min_length=6, max_length=20,
        widget=forms.PasswordInput(attrs={'placeholder': 'New Password'}),
        label='New Password'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Repeat Password'}),
        label='Confirm Password'
    )

    def __init__(self, *args, **kwargs):
        usr = kwargs.pop('usr', None)
        super().__init__(*args, **kwargs)
        self.user = usr

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        user = self.user
        if user and not authenticate(username=user.username, password=old_password):
            raise forms.ValidationError("Incorrect old password.")
        return old_password

    def clean_new_password(self):
        new_password1 = self.cleaned_data.get('new_password')
        new_password2 = self.cleaned_data.get('confirm_password')
        if new_password1 != new_password2:
            raise forms.ValidationError("The two password fields didn't match.")
        return new_password2


class LoginForm(forms.Form):
    email = forms.EmailField(
        min_length=6, max_length=40,
        widget=forms.TextInput(attrs={'placeholder': 'Email Address'})
    )
    password = forms.CharField(
        min_length=6, max_length=20,
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )


class JobForm(forms.ModelForm):
    job_title = forms.CharField(
        min_length=10, max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Job Title'})
    )
    ads = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        required=False, validators=[validate_file_extension]
    )
    total_position = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Total Number of Positions'})
    )
    job_description = forms.CharField(
        min_length=25, max_length=1000, required=False,
        widget=forms.Textarea(attrs={'rows': '8', 'class': 'form-control', 'placeholder': 'Write Job Description'})
    )

    class Meta:
        model = Jobs
        fields = ('job_title', 'last_date', 'ads', 'total_position', 'job_description')
        widgets = {
            'input_formats': settings.DATE_INPUT_FORMATS,
            'last_date': forms.DateInput(attrs={'class': 'datepicker form-control', 'placeholder': 'YYYY-MM-DD'}),
        }


class JobEditForm(forms.ModelForm):
    job_title = forms.CharField(
        min_length=10, max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Job Title'})
    )
    ads = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        required=False, validators=[validate_file_extension]
    )
    is_active = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'custom-checkbox'}),
        required=False
    )
    job_description = forms.CharField(
        min_length=25, max_length=1000, required=False,
        widget=forms.Textarea(attrs={'rows': '8', 'class': 'form-control', 'placeholder': 'Write Job Description'})
    )

    class Meta:
        model = Jobs
        fields = ('job_title', 'last_date', 'ads', 'is_active', 'job_description')
        widgets = {
            'input_formats': settings.DATE_INPUT_FORMATS,
            'last_date': forms.DateInput(attrs={'class': 'datepicker form-control', 'placeholder': 'DD/MM/YYYY'}),
        }


class EmailForm(forms.ModelForm):
    email_title = forms.CharField(
        min_length=10, max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Email Title'})
    )
    email_description = forms.CharField(
        min_length=25, max_length=1000, required=False,
        widget=forms.Textarea(attrs={'rows': '8', 'class': 'form-control', 'placeholder': 'Write Email Description'})
    )

    class Meta:
        model = EmailContent
        fields = ('email_title', 'email_description')


class EmailEditForm(forms.ModelForm):
    email_title = forms.CharField(
        min_length=10, max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Email Title'})
    )
    is_active = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'custom-checkbox'}),
        required=False
    )
    email_description = forms.CharField(
        min_length=25, max_length=1000, required=False,
        widget=forms.Textarea(attrs={'rows': '8', 'class': 'form-control', 'placeholder': 'Write Email Description'})
    )

    class Meta:
        model = EmailContent
        fields = ('email_title', 'is_active', 'email_description')


class AppliedJobForm(forms.ModelForm):
    current_salary = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Current Salary'})
    )
    expected_salary = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Expected Salary'})
    )

    class Meta:
        model = AppliedJob
        fields = ('current_salary', 'expected_salary')


class ApplicantPersonalInfoForm(forms.ModelForm):
    user_full_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'Complete Name', 'class': 'form-control'})
    )
    user_email = forms.EmailField(
        min_length=6, max_length=40,
        widget=forms.TextInput(attrs={'placeholder': 'Email Address', 'class': 'form-control'})
    )
    user_contact_no = forms.CharField(
        min_length=6, max_length=15,
        widget=forms.TextInput(attrs={'placeholder': 'Contact Number', 'class': 'form-control'})
    )
    user_degree = forms.CharField(
        min_length=6, max_length=15,
        widget=forms.TextInput(attrs={'placeholder': 'Degree Detail', 'class': 'form-control'})
    )
    user_portfolio = forms.CharField(
        min_length=6, max_length=25, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Portfolio Detail', 'class': 'form-control'})
    )
    user_tag_line = forms.CharField(
        min_length=6, max_length=25, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Tagline Detail', 'class': 'form-control'})
    )
    user_experience = forms.IntegerField(
        widget=forms.TextInput(attrs={'placeholder': 'Years of Experience', 'class': 'form-control'})
    )
    user_image = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        required=False, validators=[validate_file_extension]
    )
    user_facebook = forms.CharField(
        min_length=6, max_length=25, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Portfolio Detail', 'class': 'form-control'})
    )
    user_linkedin = forms.CharField(
        min_length=6, max_length=25, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Portfolio Detail', 'class': 'form-control'})
    )
    user_skype = forms.CharField(
        min_length=6, max_length=25, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Portfolio Detail', 'class': 'form-control'})
    )
    user_twitter = forms.CharField(
        min_length=6, max_length=25, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Portfolio Detail', 'class': 'form-control'})
    )
    user_instagram = forms.CharField(
        min_length=6, max_length=25, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Portfolio Detail', 'class': 'form-control'})
    )
    user_address = forms.CharField(
        min_length=6, max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Portfolio Detail', 'class': 'form-control'})
    )
    about_description = forms.CharField(
        max_length=1000, required=False,
        widget=forms.Textarea(attrs={'rows': '8', 'class': 'form-control', 'placeholder': 'Write Job Description'})
    )

    class Meta:
        model = ResumePersonalInfo
        fields = ('user_full_name', 'user_email', 'user_dob', 'user_contact_no', 'user_degree', 'user_portfolio',
                  'user_tag_line', 'user_experience', 'user_image', 'user_facebook', 'user_linkedin', 'user_skype',
                  'user_twitter', 'user_instagram', 'user_address', 'about_description')
        widgets = {
            'input_formats': settings.DATE_INPUT_FORMATS,
            'user_dob': forms.DateInput(attrs={'class': 'datepicker form-control', 'placeholder': 'YYYY-MM-DD'}),
        }


class ApplicantEducationInfoForm(forms.ModelForm):
    degree_category = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'Degree Category', 'class': 'form-control'})
    )
    degree_image = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        required=False, validators=[validate_file_extension]
    )
    degree_description = forms.CharField(
        min_length=25, max_length=1000, required=False,
        widget=forms.Textarea(
            attrs={
                'rows': '8',
                'class': 'form-control ckeditor-instance',
                'placeholder': 'Write Degree Description'
            }
        )
    )

    class Meta:
        model = ResumeEducationInfo
        fields = ('degree_category', 'start_degree', 'end_degree', 'degree_image', 'degree_description')
        widgets = {
            'input_formats': settings.DATE_INPUT_FORMATS,
            'start_degree': forms.DateInput(attrs={'class': 'datepicker form-control', 'placeholder': 'YYYY-MM-DD'}),
            'end_degree': forms.DateInput(attrs={'class': 'datepicker form-control', 'placeholder': 'YYYY-MM-DD'}),
        }


class ApplicantProfessionalInfoForm(forms.ModelForm):
    company_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'Company Name', 'class': 'form-control'})
    )
    job_title = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Job Title', 'class': 'form-control'})
    )
    official_description = forms.CharField(
        min_length=25, max_length=1000, required=False,
        widget=forms.Textarea(
            attrs={
                'rows': '8',
                'class': 'form-control ckeditor-instance',
                'placeholder': 'Write Job Description'
            }
        )
    )

    class Meta:
        model = ProfessionalExperienceInfo
        fields = ('company_name', 'job_title', 'start_experience', 'end_experience', 'official_description')
        widgets = {
            'input_formats': settings.DATE_INPUT_FORMATS,
            'start_experience': forms.DateInput(
                attrs={'class': 'datepicker form-control', 'placeholder': 'YYYY-MM-DD'}
            ),
            'end_experience': forms.DateInput(
                attrs={'class': 'datepicker form-control', 'placeholder': 'YYYY-MM-DD'}
            ),
        }


class ApplicantCertificateInfoForm(forms.ModelForm):
    cert_title = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'Certificate Title', 'class': 'form-control'})
    )
    cert_image = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        required=False, validators=[validate_file_extension]
    )
    cert_description = forms.CharField(
        min_length=25, max_length=1000, required=False,
        widget=forms.Textarea(
            attrs={
                'rows': '8',
                'class': 'form-control ckeditor-instance',
                'placeholder': 'Write Certificate Description'
            }
        )
    )

    class Meta:
        model = CertificateInfo
        fields = ('cert_title', 'cert_image', 'cert_description')


class ApplicantSkillInfoForm(forms.ModelForm):
    SKILLS_CHOICES = [
        ('', 'Select Percentage'),
        ('10', '10 %'),
        ('20', '20 %'),
        ('30', '30 %'),
        ('40', '40 %'),
        ('50', '50 %'),
        ('60', '60 %'),
        ('70', '70 %'),
        ('80', '80 %'),
        ('90', '90 %'),
        ('100', '100 %'),
    ]
    skill_type = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'Skill Name', 'class': 'form-control'})
    )
    skill_value = forms.ChoiceField(
        choices=SKILLS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = SkillInfo
        fields = ('skill_type', 'skill_value')



