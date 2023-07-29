"""Avatar utils"""
from base64 import b64encode
from functools import cache as funccache
from hashlib import md5
from typing import TYPE_CHECKING, Optional
from urllib.parse import urlencode

from django.core.cache import cache
from django.templatetags.static import static
from lxml import etree  # nosec
from lxml.etree import Element, SubElement  # nosec
from requests.exceptions import RequestException

from authentik.lib.config import CONFIG, get_path_from_dict
from authentik.lib.utils.http import get_http_session

GRAVATAR_URL = "https://secure.gravatar.com"
DEFAULT_AVATAR = static("dist/assets/images/user_default.png")
CACHE_KEY_GRAVATAR = "goauthentik.io/lib/avatars/"

if TYPE_CHECKING:
    from authentik.core.models import User

SVG_XML_NS = "http://www.w3.org/2000/svg"
SVG_NS_MAP = {None: SVG_XML_NS}
# Match fonts used in web UI
SVG_FONTS = [
    "'RedHatText'",
    "'Overpass'",
    "overpass",
    "helvetica",
    "arial",
    "sans-serif",
]


def avatar_mode_none(user: "User", mode: str) -> Optional[str]:
    """No avatar"""
    return DEFAULT_AVATAR


def avatar_mode_attribute(user: "User", mode: str) -> Optional[str]:
    """Avatars based on a user attribute"""
    avatar = get_path_from_dict(user.attributes, mode[11:], default=None)
    return avatar


def avatar_mode_gravatar(user: "User", mode: str) -> Optional[str]:
    """Gravatar avatars"""
    # gravatar uses md5 for their URLs, so md5 can't be avoided
    mail_hash = md5(user.email.lower().encode("utf-8")).hexdigest()  # nosec
    parameters = [("size", "158"), ("rating", "g"), ("default", "404")]
    gravatar_url = f"{GRAVATAR_URL}/avatar/{mail_hash}?{urlencode(parameters, doseq=True)}"

    full_key = CACHE_KEY_GRAVATAR + mail_hash
    if cache.has_key(full_key):
        cache.touch(full_key)
        return cache.get(full_key)

    try:
        # Since we specify a default of 404, do a HEAD request
        # (HEAD since we don't need the body)
        # so if that returns a 404, move onto the next mode
        res = get_http_session().head(gravatar_url, timeout=5)
        if res.status_code == 404:
            cache.set(full_key, None)
            return None
        res.raise_for_status()
    except RequestException:
        return gravatar_url
    cache.set(full_key, gravatar_url)
    return gravatar_url


def generate_colors(text: str) -> tuple[str, str]:
    """Generate colours based on `text`"""
    color = int(md5(text.lower().encode("utf-8")).hexdigest(), 16) % 0xFFFFFF  # nosec

    # Get a (somewhat arbitrarily) reduced scope of colors
    # to avoid too dark or light backgrounds
    blue = min(max((color) & 0xFF, 55), 200)
    green = min(max((color >> 8) & 0xFF, 55), 200)
    red = min(max((color >> 16) & 0xFF, 55), 200)
    bg_hex = f"{red:02x}{green:02x}{blue:02x}"
    # Contrasting text color (https://stackoverflow.com/a/3943023)
    text_hex = "000" if (red * 0.299 + green * 0.587 + blue * 0.114) > 186 else "fff"
    return bg_hex, text_hex


@funccache
# pylint: disable=too-many-arguments,too-many-locals
def generate_avatar_from_name(
    name: str,
    length: int = 2,
    size: int = 64,
    rounded: bool = False,
    font_size: float = 0.4375,
    bold: bool = False,
    uppercase: bool = True,
) -> str:
    """ "Generate an avatar with initials in SVG format.

    Inspired from: https://github.com/LasseRafn/ui-avatars
    """
    name_parts = name.split()
    # Only abbreviate first and last name
    if len(name_parts) > 2:
        name_parts = [name_parts[0], name_parts[-1]]

    if len(name_parts) == 1:
        initials = name_parts[0][:length]
    else:
        initials = "".join([part[0] for part in name_parts[:-1]])
        initials += name_parts[-1]
        initials = initials[:length]

    bg_hex, text_hex = generate_colors(name)

    half_size = size // 2
    shape = "circle" if rounded else "rect"
    font_weight = "600" if bold else "400"

    root_element: Element = Element(f"{{{SVG_XML_NS}}}svg", nsmap=SVG_NS_MAP)
    root_element.attrib["width"] = f"{size}px"
    root_element.attrib["height"] = f"{size}px"
    root_element.attrib["viewBox"] = f"0 0 {size} {size}"
    root_element.attrib["version"] = "1.1"

    shape = SubElement(root_element, f"{{{SVG_XML_NS}}}{shape}", nsmap=SVG_NS_MAP)
    shape.attrib["fill"] = f"#{bg_hex}"
    shape.attrib["cx"] = f"{half_size}"
    shape.attrib["cy"] = f"{half_size}"
    shape.attrib["width"] = f"{size}"
    shape.attrib["height"] = f"{size}"
    shape.attrib["r"] = f"{half_size}"

    text = SubElement(root_element, f"{{{SVG_XML_NS}}}text", nsmap=SVG_NS_MAP)
    text.attrib["x"] = "50%"
    text.attrib["y"] = "50%"
    text.attrib["style"] = (
        f"color: #{text_hex}; " "line-height: 1; " f"font-family: {','.join(SVG_FONTS)}; "
    )
    text.attrib["fill"] = f"#{text_hex}"
    text.attrib["alignment-baseline"] = "middle"
    text.attrib["dominant-baseline"] = "middle"
    text.attrib["text-anchor"] = "middle"
    text.attrib["font-size"] = f"{round(size * font_size)}"
    text.attrib["font-weight"] = f"{font_weight}"
    text.attrib["dy"] = ".1em"
    text.text = initials if not uppercase else initials.upper()

    return etree.tostring(root_element).decode()


def avatar_mode_generated(user: "User", mode: str) -> Optional[str]:
    """Wrapper that converts generated avatar to base64 svg"""
    svg = generate_avatar_from_name(user.name if user.name.strip() != "" else "a k")
    return f"data:image/svg+xml;base64,{b64encode(svg.encode('utf-8')).decode('utf-8')}"


def avatar_mode_url(user: "User", mode: str) -> Optional[str]:
    """Format url"""
    mail_hash = md5(user.email.lower().encode("utf-8")).hexdigest()  # nosec
    return mode % {
        "username": user.username,
        "mail_hash": mail_hash,
        "upn": user.attributes.get("upn", ""),
    }


def get_avatar(user: "User") -> str:
    """Get avatar with configured mode"""
    mode_map = {
        "none": avatar_mode_none,
        "initials": avatar_mode_generated,
        "gravatar": avatar_mode_gravatar,
    }
    modes: str = CONFIG.get("avatars", "none")
    for mode in modes.split(","):
        avatar = None
        if mode in mode_map:
            avatar = mode_map[mode](user, mode)
        elif mode.startswith("attributes."):
            avatar = avatar_mode_attribute(user, mode)
        elif "://" in mode:
            avatar = avatar_mode_url(user, mode)
        if avatar:
            return avatar
    return avatar_mode_none(user, modes)
