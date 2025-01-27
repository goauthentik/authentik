"""Email utility functions"""


def mask_email(email: str | None) -> str | None:
    """Mask email address for privacy

    Args:
        email: Email address to mask
    Returns:
        Masked email address or None if input is None
    Example:
        mask_email("myname@company.org")
        'm*****@c******.org'
    """
    if not email:
        return None

    local, domain = email.split("@")
    domain_parts = domain.split(".")
    limit = 2

    # Mask local part (keep first char)
    if len(local) <= limit:
        masked_local = "*" * len(local)
    else:
        masked_local = local[0] + "*" * (len(local) - 1)

    # Mask each domain part except the last one (TLD)
    masked_domain_parts = []
    for _i, part in enumerate(domain_parts[:-1]):  # Process all parts except TLD
        if len(part) <= limit:
            masked_part = "*" * len(part)
        else:
            masked_part = part[0] + "*" * (len(part) - 1)
        masked_domain_parts.append(masked_part)

    # Add TLD unchanged
    masked_domain_parts.append(domain_parts[-1])

    return f"{masked_local}@{'.'.join(masked_domain_parts)}"
