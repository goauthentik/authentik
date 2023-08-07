"""Blueprint JSON decoder"""
from rest_framework.parsers import JSONParser
from json import JSONDecoder
from typing import Any

from yaml import ScalarNode, SequenceNode

from authentik.blueprints.v1.common import BlueprintLoader, YAMLTag, yaml_key_map

TAG_KEY = "goauthentik.io/yaml-key"
ARGS_KEY = "args"


class BlueprintJSONDecoder(JSONDecoder):
    """Blueprint JSON decoder, allows using tag logic
    when using JSON data (e.g. through the API)"""

    dummy_loader: BlueprintLoader
    tag_map: dict[str, type[YAMLTag]]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, object_hook=self.object_hook, **kwargs)
        self.dummy_loader = BlueprintLoader("")
        self.tag_map = yaml_key_map()

    def parse_yaml_tag(self, data: dict) -> YAMLTag | None:
        """parse the tag"""
        yaml_tag = data.get(TAG_KEY)
        tag_cls = self.tag_map.get(yaml_tag)
        if not tag_cls:
            return None
        return tag_cls

    def parse_yaml_tag_args(self, data: Any) -> Any:
        """Parse args into their yaml equivalent"""
        if data:
            if isinstance(data, list):
                return SequenceNode(
                    "tag:yaml.org,2002:seq", [self.parse_yaml_tag_args(x) for x in data]
                )
            if isinstance(data, str):
                return ScalarNode("tag:yaml.org,2002:str", data)
            if isinstance(data, int):
                return ScalarNode("tag:yaml.org,2002:int", data)
            if isinstance(data, float):
                return ScalarNode("tag:yaml.org,2002:float", data)
        return None

    def object_hook(self, data: dict) -> dict | Any:
        if TAG_KEY not in data:
            return data
        tag_cls = self.parse_yaml_tag(data)
        if not tag_cls:
            return data
        tag_args = self.parse_yaml_tag_args(data.get(ARGS_KEY, []))
        return tag_cls(self.dummy_loader, tag_args)


class BlueprintJSONParser(JSONParser):
    """Wrapper around the rest_framework JSON parser that uses the `BlueprintJSONDecoder`"""

    def parse(self, stream, media_type=None, parser_context=None):
        parser_context = parser_context or {}
        parser_context["cls"] = BlueprintJSONDecoder
        return super().parse(stream, media_type, parser_context)
