from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from contact.models import Lead
from core.models import SiteSettings
from projects.models import Project
from services.models import Service
from team.models import TeamMember


class DashboardModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect, forms.ClearableFileInput)):
                field.widget.attrs.setdefault("class", "form-control form-control-special")
            else:
                field.widget.attrs.setdefault("class", "form-control")


class ServiceForm(DashboardModelForm):
    class Meta:
        model = Service
        fields = [
            "title",
            "slug",
            "short_description",
            "description",
            "icon",
            "cover_image",
            "is_active",
            "order",
            "meta_title",
            "meta_description",
        ]
        labels = {
            "title": "Xizmat nomi",
            "slug": "URL nomi",
            "short_description": "Qisqa tavsif",
            "description": "To‘liq tavsif",
            "icon": "Ikonka",
            "cover_image": "Muqova rasmi",
            "is_active": "Faol",
            "order": "Tartib raqami",
            "meta_title": "SEO sarlavhasi",
            "meta_description": "SEO tavsifi",
        }
        widgets = {"description": forms.Textarea(attrs={"rows": 6})}

    def clean_slug(self):
        slug = self.cleaned_data.get("slug") or slugify(self.cleaned_data.get("title", ""))
        matches = Service.objects.filter(slug=slug)
        if self.instance.pk:
            matches = matches.exclude(pk=self.instance.pk)
        if matches.exists():
            raise ValidationError("Bu slug bilan xizmat mavjud. Boshqa slug tanlang.")
        return slug


class ProjectForm(DashboardModelForm):
    technologies_text = forms.CharField(
        label="Texnologiyalar",
        required=False,
        help_text="Texnologiyalarni vergul yoki yangi qator bilan ajrating.",
        widget=forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
    )

    class Meta:
        model = Project
        fields = [
            "title",
            "slug",
            "summary",
            "description",
            "cover_image",
            "project_url",
            "is_featured",
            "is_published",
            "order",
            "meta_title",
            "meta_description",
        ]
        labels = {
            "title": "Loyiha nomi",
            "slug": "URL nomi",
            "summary": "Qisqa tavsif",
            "description": "To‘liq tavsif",
            "cover_image": "Muqova rasmi",
            "project_url": "Loyiha havolasi",
            "is_featured": "Tanlangan loyiha",
            "is_published": "Nashr qilingan",
            "order": "Tartib raqami",
            "meta_title": "SEO sarlavhasi",
            "meta_description": "SEO tavsifi",
        }
        widgets = {"description": forms.Textarea(attrs={"rows": 6})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["technologies_text"].initial = ", ".join(self.instance.technologies or [])

    def clean_slug(self):
        slug = self.cleaned_data.get("slug") or slugify(self.cleaned_data.get("title", ""))
        matches = Project.objects.filter(slug=slug)
        if self.instance.pk:
            matches = matches.exclude(pk=self.instance.pk)
        if matches.exists():
            raise ValidationError("Bu slug bilan loyiha mavjud. Boshqa slug tanlang.")
        return slug

    def save(self, commit=True):
        project = super().save(commit=False)
        project.technologies = [
            item.strip()
            for item in self.cleaned_data["technologies_text"].replace("\n", ",").split(",")
            if item.strip()
        ]
        if commit:
            project.save()
            self.save_m2m()
        return project


class TeamMemberForm(DashboardModelForm):
    class Meta:
        model = TeamMember
        fields = [
            "name",
            "position",
            "bio",
            "photo",
            "telegram_url",
            "linkedin_url",
            "is_active",
            "order",
        ]
        labels = {
            "name": "Ism-familiya",
            "position": "Lavozim",
            "bio": "Qisqacha ma’lumot",
            "photo": "Rasm",
            "telegram_url": "Telegram havolasi",
            "linkedin_url": "LinkedIn havolasi",
            "is_active": "Faol",
            "order": "Tartib raqami",
        }
        widgets = {"bio": forms.Textarea(attrs={"rows": 5})}


class SiteSettingsForm(DashboardModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            "company_name",
            "tagline",
            "footer_text",
            "logo",
            "favicon",
            "phone",
            "email",
            "address",
            "telegram_username",
            "instagram_url",
            "linkedin_url",
            "experience_stat",
            "projects_stat",
            "support_stat",
            "meta_title",
            "meta_description",
        ]
        labels = {
            "company_name": "Kompaniya nomi",
            "tagline": "Qisqa ta’rif",
            "footer_text": "Footer matni",
            "logo": "Logo rasmi",
            "favicon": "Favicon",
            "phone": "Telefon",
            "email": "Email",
            "address": "Manzil",
            "telegram_username": "Telegram foydalanuvchi nomi",
            "instagram_url": "Instagram havolasi",
            "linkedin_url": "LinkedIn havolasi",
            "experience_stat": "Tajriba ko‘rsatkichi",
            "projects_stat": "Loyihalar ko‘rsatkichi",
            "support_stat": "Qo‘llab-quvvatlash ko‘rsatkichi",
            "meta_title": "SEO sarlavhasi",
            "meta_description": "SEO tavsifi",
        }
        widgets = {"meta_description": forms.Textarea(attrs={"rows": 4})}


class LeadFilterForm(forms.Form):
    q = forms.CharField(label="Qidiruv", required=False)
    status = forms.ChoiceField(
        label="Holat",
        required=False,
        choices=[("", "Barcha holatlar"), *Lead.STATUS_CHOICES],
    )
    date_from = forms.DateField(label="Sanadan", required=False, widget=forms.DateInput(attrs={"type": "date"}))
    date_to = forms.DateField(label="Sanagacha", required=False, widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class LeadStatusForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ["status", "admin_notes"]
        labels = {"status": "Holat", "admin_notes": "Ichki izoh"}
        widgets = {"admin_notes": forms.Textarea(attrs={"rows": 4, "class": "form-control"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["status"].widget.attrs["class"] = "form-control"
