import re
import threading

from django.db import IntegrityError, transaction
from django.utils import timezone
from deep_translator.exceptions import TooManyRequests

from .i18n import (
    FALLBACK_LANGUAGE,
    LANGUAGE_CODES,
    has_complete_translation,
    translation_source_hash,
)

SOURCE_LANGUAGE = FALLBACK_LANGUAGE
TARGET_LANGUAGES = tuple(code for code in LANGUAGE_CODES if code != SOURCE_LANGUAGE)
MAX_TRANSLATION_LENGTH = 5000
REQUEST_TIMEOUT = (3, 8)
PROTECTED_TOKEN_PATTERN = re.compile(
    r"https?://[^\s<>()]+|www\.[^\s<>()]+|"
    r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|"
    r"(?<!\w)\+?\d[\d().\s-]{6,}\d(?!\w)|"
    r"```[\s\S]*?```|`[^`\n]+`"
)

_TRANSLATOR_LOCK = threading.RLock()


class TranslationServiceError(Exception):
    pass


class _RequestsWithTimeout:
    def __init__(self, requests_module):
        self._requests = requests_module

    def get(self, *args, **kwargs):
        kwargs.setdefault("timeout", REQUEST_TIMEOUT)
        return self._requests.get(*args, **kwargs)


def translate_text(text, target_language):
    if target_language not in TARGET_LANGUAGES:
        raise TranslationServiceError("Unsupported target language.")
    if not isinstance(text, str):
        raise TranslationServiceError("Only text content can be translated.")
    if len(text) > MAX_TRANSLATION_LENGTH:
        raise TranslationServiceError("Text exceeds the translation service limit.")
    if any(ord(character) < 32 and character not in "\n\r\t" for character in text):
        raise TranslationServiceError("Text contains unsupported control characters.")

    cleaned_text = text.strip()
    if not cleaned_text:
        return ""

    protected = []

    def replace_token(match):
        marker = f"BYTECOREKEEP{len(protected)}TOKEN"
        protected.append((marker, match.group(0)))
        return marker

    safe_text = PROTECTED_TOKEN_PATTERN.sub(replace_token, cleaned_text)
    if len(safe_text) > MAX_TRANSLATION_LENGTH:
        raise TranslationServiceError("Protected text exceeds the translation service limit.")

    try:
        from deep_translator import GoogleTranslator
        from deep_translator import google
    except ImportError as exc:
        raise TranslationServiceError("deep-translator is not installed.") from exc

    try:
        translator = GoogleTranslator(source=SOURCE_LANGUAGE, target=target_language)
        with _TRANSLATOR_LOCK:
            original_requests = google.requests
            google.requests = _RequestsWithTimeout(original_requests)
            try:
                translated = translator.translate(safe_text)
            finally:
                google.requests = original_requests
    except TooManyRequests as exc:
        raise TranslationServiceError(
            "Google Translate vaqtinchalik so'rovlarni chekladi. "
            "Biroz kutib, keyin qayta urinib ko'ring."
        ) from exc
    except Exception as exc:
        raise TranslationServiceError(
            f"Google Translate request failed ({type(exc).__name__})."
        ) from exc
    if not isinstance(translated, str) or not translated.strip():
        raise TranslationServiceError("Google Translate returned an empty result.")
    translated = translated.strip()
    for marker, original in protected:
        marker_pattern = re.compile(re.escape(marker), re.IGNORECASE)
        if not marker_pattern.search(translated):
            raise TranslationServiceError("The translation provider changed a protected URL, code, or identifier.")
        translated = marker_pattern.sub(lambda _: original, translated)
    return translated


def _get_or_create_locked(instance, language):
    relation = instance.translations
    manager = relation.model.objects
    foreign_key = relation.field.name
    try:
        translation = manager.select_for_update().get(**{foreign_key: instance, "language": language})
        return translation, False
    except manager.model.DoesNotExist:
        try:
            with transaction.atomic():
                translation = manager.create(**{foreign_key: instance, "language": language})
            return manager.select_for_update().get(pk=translation.pk), True
        except IntegrityError:
            return (
                manager.select_for_update().get(**{foreign_key: instance, "language": language}),
                False,
            )


def _complete_required_fields(source, translation, fields, required_fields):
    return has_complete_translation(source, translation, fields, required_fields)


def translate_instance(instance, languages=None, overwrite_manual=False):
    """Translate configured text fields, committing each language separately."""
    fields = getattr(instance, "translation_fields", ())
    required_fields = getattr(instance, "translation_required_fields", ())
    if not instance.pk or not fields:
        raise ValueError("A saved translatable object with translation_fields is required.")

    requested_languages = tuple(languages or TARGET_LANGUAGES)
    if not requested_languages or any(language not in TARGET_LANGUAGES for language in requested_languages):
        raise ValueError("Only supported non-Uzbek target languages can be translated.")

    source_hash = translation_source_hash(instance, fields)
    results = {}
    for language in requested_languages:
        with transaction.atomic():
            translation, created = _get_or_create_locked(instance, language)
            current_values = {
                field: getattr(translation, field, "") or ""
                for field in fields
            }
            manual_fields = (
                {field for field, value in current_values.items() if value}
                if translation.is_manual and not created
                else set()
            )
            same_source = translation.source_hash == source_hash
            all_source_fields_present = all(
                not (getattr(instance, field, "") or "") or current_values[field]
                for field in fields
            )
            retrying_same_source = (
                translation.status == translation.STATUS_FAILED
                and same_source
                and not translation.is_manual
            )

            if (
                translation.status == translation.STATUS_TRANSLATING
                and same_source
                and not translation.translation_attempt_expired()
            ):
                results[language] = translation.STATUS_TRANSLATING
                continue
            if (
                translation.status == translation.STATUS_COMPLETE
                and same_source
                and all_source_fields_present
                and not (overwrite_manual and manual_fields)
            ):
                results[language] = translation.STATUS_COMPLETE
                continue

            source_changed_for_manual = bool(manual_fields and not same_source)
            translation.status = translation.STATUS_TRANSLATING
            translation.attempt_started_at = timezone.now()
            if overwrite_manual or not manual_fields:
                translation.is_manual = False
                translation.source_hash = source_hash
            translation.last_error = ""
            translation.save()

        translated_values = {}
        error = ""
        for field in fields:
            source_text = getattr(instance, field, "") or ""
            if not source_text or (field in manual_fields and not overwrite_manual):
                continue
            if (
                retrying_same_source
                and current_values[field]
            ):
                continue
            try:
                translated_value = translate_text(source_text, language)
                max_length = translation._meta.get_field(field).max_length
                if max_length is not None and len(translated_value) > max_length:
                    raise TranslationServiceError("Translated text exceeds the database field limit.")
                translated_values[field] = translated_value
            except TranslationServiceError as exc:
                error = str(exc)[:255]
                break

        with transaction.atomic():
            translation = (
                translation.__class__.objects.select_for_update()
                .get(pk=translation.pk)
            )
            for field, value in translated_values.items():
                setattr(translation, field, value)

            translation.last_error = error
            translation.attempt_started_at = None
            if error:
                translation.status = translation.STATUS_FAILED
                results[language] = translation.STATUS_FAILED
            elif source_changed_for_manual and not overwrite_manual:
                translation.status = translation.STATUS_STALE
                results[language] = translation.STATUS_STALE
            elif _complete_required_fields(instance, translation, fields, required_fields):
                translation.status = translation.STATUS_COMPLETE
                translation.source_hash = source_hash
                translation.translated_at = timezone.now()
                results[language] = translation.STATUS_COMPLETE
            else:
                translation.status = translation.STATUS_PENDING
                results[language] = translation.STATUS_PENDING

            translation._automatic_translation = True
            translation.save()

        instance._translation_map_cache = None

    return results


def ensure_language_translation(instance, language):
    """Create a missing language once on demand; failed attempts need admin retry."""
    if language not in TARGET_LANGUAGES or not instance.pk:
        return None

    existing = instance._translation_map().get(language)
    if existing:
        if instance.translation_is_current(existing):
            return existing.status
        if existing.is_manual and existing.source_hash != translation_source_hash(instance):
            return existing.STATUS_STALE
        if existing.status == existing.STATUS_FAILED:
            return existing.status
        if (
            existing.status == existing.STATUS_TRANSLATING
            and not existing.translation_attempt_expired()
        ):
            return existing.status

    result = translate_instance(instance, languages=(language,))[language]
    instance._translation_map_cache = None
    return result
