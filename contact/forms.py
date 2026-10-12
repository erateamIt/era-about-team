from django import forms
import re

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
            "full_name": "Ism-familiya",
            "company": "Kompaniya",
            "email": "Email",
            "phone": "Telefon",
            "project_type": "Loyiha turi",
            "message": "Loyiha haqida",
        }
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": "Ismingiz"}),
            "company": forms.TextInput(attrs={"placeholder": "Kompaniya nomi"}),
            "email": forms.EmailInput(attrs={"placeholder": "Email"}),
            "phone": forms.TextInput(attrs={"placeholder": "+998 90 123 45 67"}),
            "project_type": forms.Select(attrs={"class": "custom-select"}),
            "message": forms.Textarea(attrs={"placeholder": "Loyihangiz haqida qisqacha ma'lumot bering...", "rows": 5}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "")
        normalized_phone = re.sub(r"[\s()-]", "", phone)
        if normalized_phone and not re.fullmatch(r"\+998\d{9}", normalized_phone):
            raise forms.ValidationError("Telefon raqami +998 bilan boshlanib, 9 ta raqamdan iborat bo‘lishi kerak.")
        return normalized_phone
