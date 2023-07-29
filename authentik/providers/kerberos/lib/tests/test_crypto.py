"""Kerberos cryptography primitives tests"""
from django.test import TestCase

from authentik.providers.kerberos.lib.crypto import (
    Aes128CtsHmacSha196,
    Aes128CtsHmacSha256128,
    Aes256CtsHmacSha196,
    Aes256CtsHmacSha384192,
    nfold,
)


class TestNfold(TestCase):
    """N-fold tests"""

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
    """aes128-cts-hmac-sha1-96 tests"""

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

    def test_encrypt_decrypt_data_identity(self):
        key = 0x9062430C8CDA3388922E6D6A509F5B7A.to_bytes(16, byteorder="big")
        plaintext = ("TESTTESTTESTTEST" * 16).encode()
        self.assertEqual(
            Aes128CtsHmacSha196.decrypt_data(
                key,
                Aes128CtsHmacSha196.encrypt_data(
                    key,
                    plaintext,
                ),
            ),
            plaintext,
        )

    def test_encrypt_decrypt_message(self):
        key = 0x9062430C8CDA3388922E6D6A509F5B7A.to_bytes(16, byteorder="big")
        confounder = 0x94B491F481485B9A0678CD3C4EA386AD.to_bytes(16, byteorder="big")
        usage = 2
        plaintext = "9 bytesss".encode()
        ciphertext = (
            0x68FB9679601F45C78857B2BF820FD6E53ECA8D42FD4B1D7024A09205ABB7CD2EC26C355D2F.to_bytes(
                37, byteorder="big"
            )
        )
        self.assertEqual(
            Aes128CtsHmacSha196.encrypt_message(key, plaintext, usage, confounder),
            ciphertext,
        )
        self.assertEqual(
            Aes128CtsHmacSha196.decrypt_message(key, ciphertext, usage),
            plaintext,
        )

    def test_encrypt_decrypt_message_identity(self):
        key = 0xFE697B52BC0D3CE14432BA036A92E65B.to_bytes(16, byteorder="big")
        plaintext = ("TESTTESTTESTTEST" * 16).encode()
        self.assertEqual(
            Aes128CtsHmacSha196.decrypt_message(
                key,
                Aes128CtsHmacSha196.encrypt_message(
                    key,
                    plaintext,
                    1,
                ),
                1,
            ),
            plaintext,
        )


class TestAes256CtsHmacSha196(TestCase):
    """aes256-cts-hmac-sha1-96 tests"""

    def test_encrypt_decrypt_data_identity(self):
        key = 0xFE697B52BC0D3CE14432BA036A92E65BBB52280990A2FA27883998D72AF30161.to_bytes(
            32, byteorder="big"
        )
        plaintext = ("TESTTESTTESTTEST" * 16).encode()
        self.assertEqual(
            Aes256CtsHmacSha196.decrypt_data(
                key,
                Aes256CtsHmacSha196.encrypt_data(
                    key,
                    plaintext,
                ),
            ),
            plaintext,
        )

    def test_encrypt_decrypt_message(self):
        key = 0xF1C795E9248A09338D82C3F8D5B567040B0110736845041347235B1404231398.to_bytes(
            32, byteorder="big"
        )
        confounder = 0xE45CA518B42E266AD98E165E706FFB60.to_bytes(16, byteorder="big")
        usage = 4
        plaintext = "30 bytes bytes bytes bytes byt".encode()
        ciphertext = 0xD1137A4D634CFECE924DBC3BF6790648BD5CFF7DE0E7B99460211D0DAEF3D79A295C688858F3B34B9CBD6EEBAE81DAF6B734D4D498B6714F1C1D.to_bytes(
            58, byteorder="big"
        )
        self.assertEqual(
            Aes256CtsHmacSha196.encrypt_message(key, plaintext, usage, confounder),
            ciphertext,
        )
        self.assertEqual(
            Aes256CtsHmacSha196.decrypt_message(key, ciphertext, usage),
            plaintext,
        )

    def test_encrypt_decrypt_message_identity(self):
        key = 0xFE697B52BC0D3CE14432BA036A92E65BBB52280990A2FA27883998D72AF30161.to_bytes(
            32, byteorder="big"
        )
        plaintext = ("TESTTESTTESTTEST" * 16).encode()
        self.assertEqual(
            Aes256CtsHmacSha196.decrypt_message(
                key,
                Aes256CtsHmacSha196.encrypt_message(
                    key,
                    plaintext,
                    1,
                ),
                1,
            ),
            plaintext,
        )

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
    """aes128-cts-hmac-sha256-128 tests"""

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

    def test_encrypt_decrypt(self):
        """
        Test cases from RFC 8009, Appendix A.

        See https://www.rfc-editor.org/rfc/rfc8009#appendix-A
        """
        key = 0x3705D96080C17728A0E800EAB6E0D23C.to_bytes(16, byteorder="big")
        # plaintext, confounder, Ke, Ki, encrypted w/o hmac, hash, ciphertext
        data = (
            (
                bytes(),
                0x7E5895EAF2672435BAD817F545A37148.to_bytes(16, byteorder="big"),
                0x9B197DD1E8C5609D6E67C3E37C62C72E.to_bytes(16, byteorder="big"),
                0x9FDA0E56AB2D85E1569A688696C26A6C.to_bytes(16, byteorder="big"),
                0xEF85FB890BB8472F4DAB20394DCA781D.to_bytes(16, byteorder="big"),
                0xAD877EDA39D50C870C0D5A0A8E48C718.to_bytes(16, byteorder="big"),
                0xEF85FB890BB8472F4DAB20394DCA781DAD877EDA39D50C870C0D5A0A8E48C718.to_bytes(
                    32, byteorder="big"
                ),
            ),
            (
                0x000102030405.to_bytes(6, byteorder="big"),
                0x7BCA285E2FD4130FB55B1A5C83BC5B24.to_bytes(16, byteorder="big"),
                0x9B197DD1E8C5609D6E67C3E37C62C72E.to_bytes(16, byteorder="big"),
                0x9FDA0E56AB2D85E1569A688696C26A6C.to_bytes(16, byteorder="big"),
                0x84D7F30754ED987BAB0BF3506BEB09CFB55402CEF7E6.to_bytes(22, byteorder="big"),
                0x877CE99E247E52D16ED4421DFDF8976C.to_bytes(16, byteorder="big"),
                0x84D7F30754ED987BAB0BF3506BEB09CFB55402CEF7E6877CE99E247E52D16ED4421DFDF8976C.to_bytes(
                    38, byteorder="big"
                ),
            ),
            (
                0x000102030405060708090A0B0C0D0E0F.to_bytes(16, byteorder="big"),
                0x56AB21713FF62C0A1457200F6FA9948F.to_bytes(16, byteorder="big"),
                0x9B197DD1E8C5609D6E67C3E37C62C72E.to_bytes(16, byteorder="big"),
                0x9FDA0E56AB2D85E1569A688696C26A6C.to_bytes(16, byteorder="big"),
                0x3517D640F50DDC8AD3628722B3569D2AE07493FA8263254080EA65C1008E8FC2.to_bytes(
                    32, byteorder="big"
                ),
                0x95FB4852E7D83E1E7C48C37EEBE6B0D3.to_bytes(16, byteorder="big"),
                0x3517D640F50DDC8AD3628722B3569D2AE07493FA8263254080EA65C1008E8FC295FB4852E7D83E1E7C48C37EEBE6B0D3.to_bytes(
                    48, byteorder="big"
                ),
            ),
            (
                0x000102030405060708090A0B0C0D0E0F1011121314.to_bytes(21, byteorder="big"),
                0xA7A4E29A4728CE10664FB64E49AD3FAC.to_bytes(16, byteorder="big"),
                0x9B197DD1E8C5609D6E67C3E37C62C72E.to_bytes(16, byteorder="big"),
                0x9FDA0E56AB2D85E1569A688696C26A6C.to_bytes(16, byteorder="big"),
                0x720F73B18D9859CD6CCB4346115CD336C70F58EDC0C4437C5573544C31C813BCE1E6D072C1.to_bytes(
                    37, byteorder="big"
                ),
                0x86B39A413C2F92CA9B8334A287FFCBFC.to_bytes(16, byteorder="big"),
                0x720F73B18D9859CD6CCB4346115CD336C70F58EDC0C4437C5573544C31C813BCE1E6D072C186B39A413C2F92CA9B8334A287FFCBFC.to_bytes(
                    53, byteorder="big"
                ),
            ),
        )

        for plaintext, confounder, ke, ki, encrypted, hash_, ciphertext in data:
            self.assertEqual(
                Aes128CtsHmacSha256128.encrypt_data(ke, confounder + plaintext),
                encrypted,
            )

            self.assertEqual(
                Aes128CtsHmacSha256128.decrypt_data(ke, encrypted),
                confounder + plaintext,
            )

            self.assertTrue(
                Aes128CtsHmacSha256128.verify_integrity(
                    key,
                    ciphertext,
                    bytes([0] * (Aes128CtsHmacSha256128.CIPHER_BLOCK_BITS // 8)) + encrypted,
                    2,
                )
            )

            self.assertEqual(
                Aes128CtsHmacSha256128.decrypt_message(
                    key, Aes128CtsHmacSha256128.encrypt_message(key, plaintext, 2), 2
                ),
                plaintext,
            )

            self.assertEqual(
                Aes128CtsHmacSha256128.integrity_hash(
                    key, bytes([0] * (Aes128CtsHmacSha256128.CIPHER_BLOCK_BITS // 8)) + encrypted, 2
                ),
                hash_,
            )


class TestAes256CtsHmacSha384192(TestCase):
    """aes256-cts-hmac-sha384-192 tests"""

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

    def test_encrypt_decrypt(self):
        """
        Test cases from RFC 8009, Appendix A.

        See https://www.rfc-editor.org/rfc/rfc8009#appendix-A
        """
        key = 0x6D404D37FAF79F9DF0D33568D320669800EB4836472EA8A026D16B7182460C52.to_bytes(
            32, byteorder="big"
        )
        # plaintext, confounder, Ke, Ki, encrypted w/o hmac, hash, ciphertext
        data = (
            (
                bytes(),
                0xF764E9FA15C276478B2C7D0C4E5F58E4.to_bytes(16, byteorder="big"),
                0x56AB22BEE63D82D7BC5227F6773F8EA7A5EB1C825160C38312980C442E5C7E49.to_bytes(
                    32, byteorder="big"
                ),
                0x69B16514E3CD8E56B82010D5C73012B622C4D00FFC23ED1F.to_bytes(24, byteorder="big"),
                0x41F53FA5BFE7026D91FAF9BE959195A0.to_bytes(16, byteorder="big"),
                0x58707273A96A40F0A01960621AC612748B9BBFBE7EB4CE3C.to_bytes(24, byteorder="big"),
                0x41F53FA5BFE7026D91FAF9BE959195A058707273A96A40F0A01960621AC612748B9BBFBE7EB4CE3C.to_bytes(
                    40, byteorder="big"
                ),
            ),
            (
                0x000102030405.to_bytes(6, byteorder="big"),
                0xB80D3251C1F6471494256FFE712D0B9A.to_bytes(16, byteorder="big"),
                0x56AB22BEE63D82D7BC5227F6773F8EA7A5EB1C825160C38312980C442E5C7E49.to_bytes(
                    32, byteorder="big"
                ),
                0x69B16514E3CD8E56B82010D5C73012B622C4D00FFC23ED1F.to_bytes(24, byteorder="big"),
                0x4ED7B37C2BCAC8F74F23C1CF07E62BC7B75FB3F637B9.to_bytes(22, byteorder="big"),
                0xF559C7F664F69EAB7B6092237526EA0D1F61CB20D69D10F2.to_bytes(24, byteorder="big"),
                0x4ED7B37C2BCAC8F74F23C1CF07E62BC7B75FB3F637B9F559C7F664F69EAB7B6092237526EA0D1F61CB20D69D10F2.to_bytes(
                    46, byteorder="big"
                ),
            ),
            (
                0x000102030405060708090A0B0C0D0E0F.to_bytes(16, byteorder="big"),
                0x53BF8A0D105265D4E276428624CE5E63.to_bytes(16, byteorder="big"),
                0x56AB22BEE63D82D7BC5227F6773F8EA7A5EB1C825160C38312980C442E5C7E49.to_bytes(
                    32, byteorder="big"
                ),
                0x69B16514E3CD8E56B82010D5C73012B622C4D00FFC23ED1F.to_bytes(24, byteorder="big"),
                0xBC47FFEC7998EB91E8115CF8D19DAC4BBBE2E163E87DD37F49BECA92027764F6.to_bytes(
                    32, byteorder="big"
                ),
                0x8CF51F14D798C2273F35DF574D1F932E40C4FF255B36A266.to_bytes(24, byteorder="big"),
                0xBC47FFEC7998EB91E8115CF8D19DAC4BBBE2E163E87DD37F49BECA92027764F68CF51F14D798C2273F35DF574D1F932E40C4FF255B36A266.to_bytes(
                    56, byteorder="big"
                ),
            ),
            (
                0x000102030405060708090A0B0C0D0E0F1011121314.to_bytes(21, byteorder="big"),
                0x763E65367E864F02F55153C7E3B58AF1.to_bytes(16, byteorder="big"),
                0x56AB22BEE63D82D7BC5227F6773F8EA7A5EB1C825160C38312980C442E5C7E49.to_bytes(
                    32, byteorder="big"
                ),
                0x69B16514E3CD8E56B82010D5C73012B622C4D00FFC23ED1F.to_bytes(24, byteorder="big"),
                0x40013E2DF58E8751957D2878BCD2D6FE101CCFD556CB1EAE79DB3C3EE86429F2B2A602AC86.to_bytes(
                    37, byteorder="big"
                ),
                0xFEF6ECB647D6295FAE077A1FEB517508D2C16B4192E01F62.to_bytes(24, byteorder="big"),
                0x40013E2DF58E8751957D2878BCD2D6FE101CCFD556CB1EAE79DB3C3EE86429F2B2A602AC86FEF6ECB647D6295FAE077A1FEB517508D2C16B4192E01F62.to_bytes(
                    61, byteorder="big"
                ),
            ),
        )

        for plaintext, confounder, ke, ki, encrypted, hash_, ciphertext in data:
            self.assertEqual(
                Aes256CtsHmacSha384192.encrypt_data(ke, confounder + plaintext),
                encrypted,
            )

            self.assertEqual(
                Aes256CtsHmacSha384192.decrypt_data(ke, encrypted),
                confounder + plaintext,
            )

            self.assertTrue(
                Aes256CtsHmacSha384192.verify_integrity(
                    key,
                    ciphertext,
                    bytes([0] * (Aes256CtsHmacSha384192.CIPHER_BLOCK_BITS // 8)) + encrypted,
                    2,
                )
            )

            self.assertEqual(
                Aes256CtsHmacSha384192.decrypt_message(
                    key, Aes256CtsHmacSha384192.encrypt_message(key, plaintext, 2), 2
                ),
                plaintext,
            )

            self.assertEqual(
                Aes256CtsHmacSha384192.integrity_hash(
                    key, bytes([0] * (Aes256CtsHmacSha384192.CIPHER_BLOCK_BITS // 8)) + encrypted, 2
                ),
                hash_,
            )
