import hashlib
import json
from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.utils.translation import get_language


LANGUAGE_CODES = ("uz", "ru", "tr", "en")
FALLBACK_LANGUAGE = "uz"
LANGUAGE_LABELS = {
    "uz": "O‘zbek",
    "ru": "Русский",
    "tr": "Türkçe",
    "en": "English",
}
LANGUAGE_CHOICES = [(code, LANGUAGE_LABELS[code]) for code in LANGUAGE_CODES]


def translation_source_hash(instance, fields=None):
    fields = fields or getattr(instance, "translation_fields", ())
    content = {field: getattr(instance, field, "") or "" for field in fields}
    return hashlib.sha256(
        json.dumps(content, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def has_complete_translation(source, translation, fields, required_fields):
    if not required_fields or not all(getattr(translation, field, "") for field in required_fields):
        return False
    return all(
        not (getattr(source, field, "") or "") or bool(getattr(translation, field, ""))
        for field in fields
    )


def normalize_language(language=None):
    code = (language or get_language() or FALLBACK_LANGUAGE).split("-")[0]
    if code in LANGUAGE_CODES:
        return code
    return FALLBACK_LANGUAGE


class TranslatableMixin:
    """Use translated content and fall back to Uzbek when a translation is missing."""

    translation_fallback_fields = ()
    translation_required_fields = ()

    def save(self, *args, **kwargs):
        fields = getattr(self, "translation_fields", ())
        old_values = None
        if self.pk and fields:
            old_values = type(self).objects.filter(pk=self.pk).values(*fields).first()
        update_fields = kwargs.get("update_fields")
        result = super().save(*args, **kwargs)
        if old_values:
            changed = any(old_values[field] != getattr(self, field) for field in fields)
            if update_fields is not None:
                changed = changed and bool(set(fields).intersection(update_fields))
            if changed:
                self.translations.exclude(language=FALLBACK_LANGUAGE).update(
                    status=TranslationBase.STATUS_STALE
                )
                self._translation_map_cache = None
        return result

    def get_translated(self, field, language=None):
        language = normalize_language(language)
        translations = self._translation_map()
        if language == FALLBACK_LANGUAGE:
            return getattr(self, field, "") or ""

        translation = translations.get(language)
        if translation and not self.translation_is_current(translation):
            return getattr(self, field, "") or ""
        value = getattr(translation, field, "") if translation else ""
        return value or getattr(self, field, "") or ""

    def translation_is_current(self, translation):
        source_fields = getattr(self, "translation_fields", ())
        return bool(
            translation.source_hash
            and translation.source_hash == translation_source_hash(self, source_fields)
            and translation.status == TranslationBase.STATUS_COMPLETE
            and has_complete_translation(
                self,
                translation,
                source_fields,
                getattr(self, "translation_required_fields", ()),
            )
        )

    def _translation_map(self):
        cached = getattr(self, "_translation_map_cache", None)
        if cached is not None:
            return cached
        related = getattr(self, "translations", None)
        mapping = {}
        if related is not None:
            mapping = {item.language: item for item in related.all()}
        self._translation_map_cache = mapping
        return mapping

    def translated_languages(self):
        filled = set()
        required_fields = self.translation_required_fields or self.translation_fallback_fields
        if required_fields and all(getattr(self, field, "") for field in required_fields):
            filled.add(FALLBACK_LANGUAGE)
        for translation in self._translation_map().values():
            if (
                required_fields
                and all(getattr(translation, field, "") for field in required_fields)
                and self.translation_is_current(translation)
            ):
                filled.add(translation.language)
        return filled

    def missing_languages(self):
        return [code for code in LANGUAGE_CODES if code not in self.translated_languages()]

    def translation_statuses(self):
        translations = self._translation_map()
        status_labels = {
            TranslationBase.STATUS_PENDING: "Kutilmoqda",
            TranslationBase.STATUS_COMPLETE: "Tayyor",
            TranslationBase.STATUS_FAILED: "Xatolik",
            TranslationBase.STATUS_STALE: "Eskirgan",
            TranslationBase.STATUS_TRANSLATING: "Tarjima kutilmoqda",
        }
        statuses = []
        for language in LANGUAGE_CODES:
            translation = translations.get(language)
            if language == FALLBACK_LANGUAGE:
                status = (
                    TranslationBase.STATUS_COMPLETE
                    if self.translation_required_fields
                    and all(getattr(self, field, "") for field in self.translation_required_fields)
                    else TranslationBase.STATUS_PENDING
                )
            elif translation and translation.status == TranslationBase.STATUS_FAILED:
                status = TranslationBase.STATUS_FAILED
            elif (
                translation
                and translation.status == TranslationBase.STATUS_TRANSLATING
                and not translation.translation_attempt_expired()
            ):
                status = TranslationBase.STATUS_TRANSLATING
            elif translation and (
                translation.status in {TranslationBase.STATUS_STALE, TranslationBase.STATUS_TRANSLATING}
                or (
                    translation.source_hash
                    and translation.source_hash != translation_source_hash(self)
                )
            ):
                status = TranslationBase.STATUS_STALE
            elif translation and self.translation_is_current(translation):
                status = TranslationBase.STATUS_COMPLETE
            elif translation and translation.status == TranslationBase.STATUS_COMPLETE:
                status = TranslationBase.STATUS_PENDING
            else:
                status = getattr(translation, "status", TranslationBase.STATUS_PENDING)
            statuses.append(
                {
                    "language": language.upper(),
                    "status": status,
                    "label": status_labels[status],
                    "error": getattr(translation, "last_error", ""),
                    "manual": bool(getattr(translation, "is_manual", False)),
                }
            )
        return statuses


class TranslationBase(models.Model):
    STATUS_PENDING = "pending"
    STATUS_COMPLETE = "complete"
    STATUS_FAILED = "failed"
    STATUS_STALE = "stale"
    STATUS_TRANSLATING = "translating"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Kutilmoqda"),
        (STATUS_COMPLETE, "Tarjima qilingan"),
        (STATUS_FAILED, "Xatolik"),
        (STATUS_STALE, "Eskirgan"),
        (STATUS_TRANSLATING, "Tarjima kutilmoqda"),
    ]

    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING)
    is_manual = models.BooleanField(default=True)
    last_error = models.CharField(max_length=255, blank=True)
    source_hash = models.CharField(max_length=64, blank=True)
    translated_at = models.DateTimeField(null=True, blank=True)
    attempt_started_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not getattr(self, "_automatic_translation", False):
            content_fields = [
                field.name
                for field in self._meta.concrete_fields
                if field.name not in {
                    "id",
                    "language",
                    "status",
                    "is_manual",
                    "last_error",
                    "source_hash",
                    "translated_at",
                    "attempt_started_at",
                }
                and not field.is_relation
            ]
            original = (
                type(self).objects.filter(pk=self.pk).values(*content_fields).first()
                if self.pk
                else None
            )
            changed = original is None or any(
                original[name] != getattr(self, name) for name in content_fields
            )
            if changed:
                self.is_manual = True
                source = self._source_object()
                required = getattr(source, "translation_required_fields", ()) if source else ()
                self.status = (
                    self.STATUS_COMPLETE
                    if source
                    and has_complete_translation(
                        source,
                        self,
                        getattr(source, "translation_fields", ()),
                        required,
                    )
                    else self.STATUS_PENDING
                )
                if source and source.pk:
                    self.source_hash = translation_source_hash(source)
                self.last_error = ""
                if kwargs.get("update_fields") is not None:
                    kwargs["update_fields"] = set(kwargs["update_fields"]) | {
                        "is_manual",
                        "status",
                        "source_hash",
                        "last_error",
                    }
        super().save(*args, **kwargs)

    def translation_attempt_expired(self):
        return not self.attempt_started_at or timezone.now() - self.attempt_started_at >= timedelta(minutes=2)

    def _source_object(self):
        for field in self._meta.concrete_fields:
            if field.is_relation and field.many_to_one:
                return getattr(self, field.name, None)
        return None
