"""Blueprint JSON decoder"""
import codecs
from collections.abc import Hashable
from typing import Any

from django.conf import settings
from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser
from yaml import load
from yaml.nodes import MappingNode

from authentik.blueprints.v1.common import BlueprintLoader, YAMLTag, yaml_key_map

TAG_KEY = "goauthentik.io/yaml-key"
ARGS_KEY = "args"


class BlueprintJSONDecoder(BlueprintLoader):
    """Blueprint JSON decoder, allows using tag logic when using JSON data (e.g. through the API,
    when YAML tags are not available).

    This is still based on a YAML Loader, since all the YAML Tag constructors expect *Node objects
    from YAML, this makes things a lot easier."""

    tag_map: dict[str, type[YAMLTag]]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tag_map = yaml_key_map()
        self.add_constructor("tag:yaml.org,2002:map", BlueprintJSONDecoder.construct_yaml_map)

    def construct_yaml_map(self, node):
        """The original construct_yaml_map creates a dict, yields it, then updates it,
        which is probably some sort of performance optimisation, however it breaks here
        when we don't return a dict from the `construct_mapping` function"""
        value = self.construct_mapping(node)
        yield value

    def construct_mapping(self, node: MappingNode, deep: bool = False) -> dict[Hashable, Any]:
        """Check if the mapping has a special key and create an in-place YAML tag for it,
        and return that instead of the actual dict"""
        parsed = super().construct_mapping(node, deep=deep)
        if TAG_KEY not in parsed:
            return parsed
        tag_cls = self.parse_yaml_tag(parsed)
        if not tag_cls:
            return parsed
        # MappingNode's value is a list of tuples where the tuples
        # consist of (KeyNode, ValueNode)
        # so this filters out the value node for `args`
        raw_args_pair = [x for x in node.value if x[0].value == ARGS_KEY]
        if len(raw_args_pair) < 1:
            return parsed
        # Get the value of the first Node in the pair we get from above
        # where the value isn't `args`, i.e. the actual argument data
        raw_args_data = [x for x in raw_args_pair[0] if x.value != ARGS_KEY][0]
        return tag_cls(self, raw_args_data)

    def parse_yaml_tag(self, data: dict) -> YAMLTag | None:
        """parse the tag"""
        yaml_tag = data.get(TAG_KEY)
        tag_cls = self.tag_map.get(yaml_tag)
        if not tag_cls:
            return None
        return tag_cls


class BlueprintJSONParser(JSONParser):
    """Wrapper around the rest_framework JSON parser that uses the `BlueprintJSONDecoder`"""

    def parse(self, stream, media_type=None, parser_context=None):
        encoding = parser_context.get("encoding", settings.DEFAULT_CHARSET)
        try:
            decoded_stream = codecs.getreader(encoding)(stream)
            return load(decoded_stream, BlueprintJSONDecoder)
        except ValueError as exc:
            raise ParseError("JSON parse error") from exc
