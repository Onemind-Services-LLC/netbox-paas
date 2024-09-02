from django.core.exceptions import ValidationError

__all__ = ('validate_comma_separated',)


def validate_comma_separated(value):
    if not isinstance(value, str):
        raise ValidationError("This field requires a string of comma-separated values.")
    values = value.split(',')
    if any(not item.strip() for item in values):
        raise ValidationError("Each value should be non-empty and comma-separated without extra spaces.")

    return value
