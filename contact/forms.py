import re

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Lead


class ContactForm(forms.ModelForm):
    website = forms.CharField(
        required=False,
        label="",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "off",
                "tabindex": "-1",
                "aria-hidden": "true",
            }
        ),
    )

    class Meta:
        model = Lead
        fields = ["full_name", "company", "email", "phone", "project_type", "message"]
        labels = {
            "full_name": _("Full name"),
            "company": _("Company"),
            "email": _("Email"),
            "phone": _("Phone"),
            "project_type": _("Project type"),
            "message": _("About the project"),
        }
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": _("Your name")}),
            "company": forms.TextInput(attrs={"placeholder": _("Company name")}),
            "email": forms.EmailInput(attrs={"placeholder": _("Email")}),
            "phone": forms.TextInput(attrs={"placeholder": "+998 90 123 45 67"}),
            "project_type": forms.Select(attrs={"class": "custom-select"}),
            "message": forms.Textarea(
                attrs={"placeholder": _("Tell us briefly about your project..."), "rows": 5}
            ),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "")
        normalized_phone = re.sub(r"[\s()-]", "", phone)
        if normalized_phone and not re.fullmatch(r"\+998\d{9}", normalized_phone):
            raise forms.ValidationError(
                _("The phone number must start with +998 and contain 9 digits.")
            )
        return normalized_phone
