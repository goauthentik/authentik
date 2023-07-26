from django.test import TestCase

from authentik.lib.kerberos.crypto import (
    Aes128CtsHmacSha196,
    Aes128CtsHmacSha256128,
    Aes256CtsHmacSha196,
    Aes256CtsHmacSha384192,
    nfold,
)


class TestNfold(TestCase):
    def test_nfold(self):
        """
        Test cases from https://www.rfc-editor.org/rfc/rfc3961#appendix-A.1
        """

        cases = (
            # data, size (in bits), output
            ("012345", 64, 0xBE072631276B1955),
            ("password", 56, 0x78A07B6CAF85FA),
            ("Rough Consensus, and Running Code", 64, 0xBB6ED30870B7F0E0),
            ("password", 168, 0x59E4A8CA7C0385C3C37B3F6D2000247CB6E6BD5B3E),
            (
                "MASSACHVSETTS INSTITVTE OF TECHNOLOGY",
                192,
                0xDB3B0D8F0B061E603282B308A50841229AD798FAB9540C1B,
            ),
            ("Q", 168, 0x518A54A215A8452A518A54A215A8452A518A54A215),
            ("ba", 168, 0xFB25D531AE8974499F52FD92EA9857C4BA24CF297E),
            # Additional with `kerberos` as data
            ("kerberos", 64, 0x6B65726265726F73),
            ("kerberos", 128, 0x6B65726265726F737B9B5B2B93132B93),
            ("kerberos", 168, 0x8372C236344E5F1550CD0747E15D62CA7A5A3BCEA4),
            ("kerberos", 256, 0x6B65726265726F737B9B5B2B93132B935C9BDCDAD95C9899C4CAE4DEE6D6CAE4),
        )

        for data, size, output in cases:
            self.assertEqual(
                nfold(data.encode(), size // 8), output.to_bytes(size // 8, byteorder="big")
            )


class TestAes128CtsHmacSha196(TestCase):
    def test_string_to_key(self):
        """
        Test cases from RFC 3962, Appendix B.

        See https://www.rfc-editor.org/rfc/rfc3962#appendix-B
        """
        data = (
            # Iteration count, password, salt, resulting key
            (1, "password", "ATHENA.MIT.EDUraeburn".encode(), 0x42263C6E89F4FC28B8DF68EE09799F15),
            (2, "password", "ATHENA.MIT.EDUraeburn".encode(), 0xC651BF29E2300AC27FA469D693BDDA13),
            (
                1200,
                "password",
                "ATHENA.MIT.EDUraeburn".encode(),
                0x4C01CD46D632D01E6DBE230A01ED642A,
            ),
            (
                5,
                "password",
                0x1234567878563412.to_bytes(8, byteorder="big"),
                0xE9B23D52273747DD5C35CB55BE619D8E,
            ),
            (
                1200,
                "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                "pass phrase equals block size".encode(),
                0x59D1BB789A828B1AA54EF9C2883F69ED,
            ),
            (
                1200,
                "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                "pass phrase exceeds block size".encode(),
                0xCB8005DC5F90179A7F02104C0018751D,
            ),
            (
                50,
                "𝄞",
                "EXAMPLE.COMpianist".encode(),
                0xF149C1F2E154A73452D43E7FE62A56E5,
            ),
        )

        for iterations, password, salt, key in data:
            self.assertEqual(
                Aes128CtsHmacSha196.string_to_key(
                    password.encode(), salt, "{:08x}".format(iterations)
                ),
                key.to_bytes(16, byteorder="big"),
            )


class TestAes256CtsHmacSha196(TestCase):
    def test_string_to_key(self):
        """
        Test cases from RFC 3962, Appendix B.

        See https://www.rfc-editor.org/rfc/rfc3962#appendix-B
        """
        data = (
            # Iteration count, password, salt, resulting key
            (
                1,
                "password",
                "ATHENA.MIT.EDUraeburn".encode(),
                0xFE697B52BC0D3CE14432BA036A92E65BBB52280990A2FA27883998D72AF30161,
            ),
            (
                2,
                "password",
                "ATHENA.MIT.EDUraeburn".encode(),
                0xA2E16D16B36069C135D5E9D2E25F896102685618B95914B467C67622225824FF,
            ),
            (
                1200,
                "password",
                "ATHENA.MIT.EDUraeburn".encode(),
                0x55A6AC740AD17B4846941051E1E8B0A7548D93B0AB30A8BC3FF16280382B8C2A,
            ),
            (
                5,
                "password",
                0x1234567878563412.to_bytes(8, byteorder="big"),
                0x97A4E786BE20D81A382D5EBC96D5909CABCDADC87CA48F574504159F16C36E31,
            ),
            (
                1200,
                "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                "pass phrase equals block size".encode(),
                0x89ADEE3608DB8BC71F1BFBFE459486B05618B70CBAE22092534E56C553BA4B34,
            ),
            (
                1200,
                "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                "pass phrase exceeds block size".encode(),
                0xD78C5C9CB872A8C9DAD4697F0BB5B2D21496C82BEB2CAEDA2112FCEEA057401B,
            ),
            (
                50,
                "𝄞",
                "EXAMPLE.COMpianist".encode(),
                0x4B6D9839F84406DF1F09CC166DB4B83C571848B784A3D6BDC346589A3E393F9E,
            ),
        )

        for iterations, password, salt, key in data:
            self.assertEqual(
                Aes256CtsHmacSha196.string_to_key(
                    password.encode(), salt, "{:08x}".format(iterations)
                ),
                key.to_bytes(32, byteorder="big"),
            )


class TestAes128CtsHmacSha256128(TestCase):
    def test_derive_key(self):
        """
        Test cases from RFC 8009, Appendix A.

        See https://www.rfc-editor.org/rfc/rfc8009#appendix-A
        """

        key = 0x3705D96080C17728A0E800EAB6E0D23C.to_bytes(16, byteorder="big")
        data = (
            # usage, derived_key
            (0x0000000299, 0xB31A018A48F54776F403E9A396325DC3),
            (0x00000002AA, 0x9B197DD1E8C5609D6E67C3E37C62C72E),
            (0x0000000255, 0x9FDA0E56AB2D85E1569A688696C26A6C),
        )
        for usage, derived_key in data:
            self.assertEqual(
                Aes128CtsHmacSha256128.derive_key(key, usage.to_bytes(5, byteorder="big")),
                derived_key.to_bytes(16, byteorder="big"),
            )

    def test_string_to_key(self):
        """
        Test cases from RFC 8009, Appendix A.

        See https://www.rfc-editor.org/rfc/rfc8009#appendix-A
        """

        data = (
            # iterations, password, salt, key
            (
                32768,
                "password",
                0x10DF9DD783E5BC8ACEA1730E74355F61.to_bytes(16, byteorder="big")
                + "ATHENA.MIT.EDUraeburn".encode(),
                0x089BCA48B105EA6EA77CA5D2F39DC5E7,
            ),
        )

        for iterations, password, salt, key in data:
            self.assertEqual(
                Aes128CtsHmacSha256128.string_to_key(
                    password.encode(), salt, "{:08x}".format(iterations)
                ),
                key.to_bytes(16, byteorder="big"),
            )


class TestAes256CtsHmacSha384192(TestCase):
    def test_derive_key(self):
        """
        Test cases from RFC 8009, Appendix A.

        See https://www.rfc-editor.org/rfc/rfc8009#appendix-A
        """

        key = 0x6D404D37FAF79F9DF0D33568D320669800EB4836472EA8A026D16B7182460C52.to_bytes(
            32, byteorder="big"
        )
        data = (
            # usage, derived_key, derived_key_length
            (0x0000000299, 0xEF5718BE86CC84963D8BBB5031E9F5C4BA41F28FAF69E73D, 24),
            (0x00000002AA, 0x56AB22BEE63D82D7BC5227F6773F8EA7A5EB1C825160C38312980C442E5C7E49, 32),
            (0x0000000255, 0x69B16514E3CD8E56B82010D5C73012B622C4D00FFC23ED1F, 24),
        )
        for usage, derived_key, derived_key_length in data:
            self.assertEqual(
                Aes256CtsHmacSha384192.derive_key(key, usage.to_bytes(5, byteorder="big")),
                derived_key.to_bytes(derived_key_length, byteorder="big"),
            )

    def test_string_to_key(self):
        """
        Test cases from RFC 8009, Appendix A.

        See https://www.rfc-editor.org/rfc/rfc8009#appendix-A
        """

        data = (
            # iterations, password, salt, key
            (
                32768,
                "password",
                0x10DF9DD783E5BC8ACEA1730E74355F61.to_bytes(16, byteorder="big")
                + "ATHENA.MIT.EDUraeburn".encode(),
                0x45BD806DBF6A833A9CFFC1C94589A222367A79BC21C413718906E9F578A78467,
            ),
        )

        for iterations, password, salt, key in data:
            self.assertEqual(
                Aes256CtsHmacSha384192.string_to_key(
                    password.encode(), salt, "{:08x}".format(iterations)
                ),
                key.to_bytes(32, byteorder="big"),
            )
