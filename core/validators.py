from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator


MAX_IMAGE_SIZE = 5 * 1024 * 1024

validate_image_extension = FileExtensionValidator(
    allowed_extensions=["jpg", "jpeg", "png", "webp", "ico"],
)


def validate_image_file(image):
    validate_image_extension(image)
    if image.size > MAX_IMAGE_SIZE:
        raise ValidationError("Rasm hajmi 5 MB dan oshmasligi kerak.")
