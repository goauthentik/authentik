"""Email utility functions"""

from email.utils import parseaddr

Address = str | tuple[str, str] | list[str | tuple[str, str]] | None


def _normalize_single_address(item: str | tuple[str, str] | list[str]) -> tuple[str, str]:
    """Normalize a single address into a (name, email) tuple."""
    if isinstance(item, tuple | list):
        if len(item) != 2:  # noqa: PLR2004
            raise ValueError("Address tuple must be in the form (name, email)")
        name, email = item
        return (str(name or "").strip(), str(email or "").strip())
    if isinstance(item, str):
        # Only parse RFC 5322 style addresses ("Name <email>"), plain addresses are kept as-is
        # so that unusual but valid addresses are not mangled by parseaddr
        if "<" in item and item.rstrip().endswith(">"):
            name, email = parseaddr(item)
            if email:
                return (name.strip(), email.strip())
        return ("", item.strip())
    raise ValueError("Address must be a string or a (name, email) tuple")


def normalize_addresses(addr: Address) -> list[tuple[str, str]] | None:
    """Normalize email address parameter to list of (name, email) tuples.

    Args:
        addr: Email address(es). Can be:
            - None: Returns None
            - Single email string: "user@example.com"
            - Formatted address string: "John Doe <user@example.com>"
            - (name, email) tuple: ("John Doe", "user@example.com")
            - List of any of the above

    Returns:
        List of (name, email) tuples suitable for TemplateEmailMessage, or None

    Raises:
        ValueError: If address list is empty or addr is not a valid type
    """
    if addr is None:
        return None
    if isinstance(addr, str | tuple):
        return [_normalize_single_address(addr)]
    if isinstance(addr, list):
        if not addr:
            raise ValueError("Address list cannot be empty")
        return [_normalize_single_address(item) for item in addr]
    raise ValueError("Address must be a string, a (name, email) tuple, or a list of those")


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
