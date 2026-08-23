"""SMS utility functions"""

# Number of trailing digits kept visible when masking a phone number.
PHONE_NUMBER_VISIBLE_DIGITS = 4


def mask_phone_number(phone_number: str | None) -> str | None:
    """Mask a phone number for privacy, keeping only the trailing digits visible.

    A leading "+" is preserved so that international numbers remain recognisable.

    Args:
        phone_number: Phone number to mask.
    Returns:
        Masked phone number, or None if input is None or empty.
    Example:
        mask_phone_number("+12025550173")
        '+*******0173'
    """
    if not phone_number:
        return None

    prefix = ""
    digits = phone_number
    if digits.startswith("+"):
        prefix = "+"
        digits = digits[1:]

    if len(digits) <= PHONE_NUMBER_VISIBLE_DIGITS:
        return prefix + "*" * len(digits)

    masked_length = len(digits) - PHONE_NUMBER_VISIBLE_DIGITS
    return prefix + "*" * masked_length + digits[-PHONE_NUMBER_VISIBLE_DIGITS:]
