"""template function tests"""

from django.template import Context
from django.test import TestCase

from authentik.stages.email.templatetags.authentik_stages_email import (
    AttachmentType,
    attach_image,
    inline_static_binary,
)


class TestTemplateTags(TestCase):
    """Template tag tests"""

    def test_inline_static_binary_does_not_exist(self):
        """Test inlining binary file"""
        filename = "this_file_should_not_exist.png"
        result = inline_static_binary(filename)
        self.assertEqual(result, filename)

    def test_inline_png(self):
        """Test inlining png"""
        result = inline_static_binary("src/assets/images/user_default.png")
        self.assertEqual(
            result,
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGP6zwAAAgcBApocMXEAAAAASUVORK5CYII=",
        )

    def test_inline_textfile(self):
        """Test inlining binary textfile"""
        result = inline_static_binary("robots.txt")
        self.assertEqual(result, "data:text/plain;base64,VXNlci1hZ2VudDogKgpEaXNhbGxvdzogLwo=")

    def test_attach_image(self):
        """Test attaching image"""
        ctx = Context({"domain": "localhost", "attachments": {}})
        result = attach_image(ctx, "src/assets/images/user_default.png")
        self.assertEqual(result, "cid:attach_0@localhost")
        self.assertEqual(
            ctx["attachments"],
            {
                "src/assets/images/user_default.png": {
                    "content_id": "attach_0@localhost",
                    "type": AttachmentType.IMAGE,
                }
            },
        )
