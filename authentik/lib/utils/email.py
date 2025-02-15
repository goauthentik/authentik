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


    try:
        # Basic email format validation
        if email.count("@") != 1:
            raise ValueError("Invalid email format: Must contain exactly one '@' symbol")

        local, domain = email.split("@")
        if not local or not domain:
            raise ValueError("Invalid email format: Local and domain parts cannot be empty")

        domain_parts = domain.split(".")
        if len(domain_parts) < 2:  # noqa: PLR2004
            raise ValueError("Invalid email format: Domain must contain at least one dot")

        limit = 2

        # Mask local part (keep first char)
        if len(local) <= limit:
            masked_local = "*" * len(local)
        else:
            masked_local = local[0] + "*" * (len(local) - 1)

        # Mask each domain part except the last one (TLD)
        masked_domain_parts = []
        for _i, part in enumerate(domain_parts[:-1]):  # Process all parts except TLD
            if not part:  # Check for empty parts (consecutive dots)
                raise ValueError("Invalid email format: Domain parts cannot be empty")
            if len(part) <= limit:
                masked_part = "*" * len(part)
            else:
                masked_part = part[0] + "*" * (len(part) - 1)
            masked_domain_parts.append(masked_part)

        # Add TLD unchanged
        if not domain_parts[-1]:  # Check if TLD is empty
            raise ValueError("Invalid email format: TLD cannot be empty")
        masked_domain_parts.append(domain_parts[-1])

        return f"{masked_local}@{'.'.join(masked_domain_parts)}"
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Invalid email format: {str(e)}") from e
