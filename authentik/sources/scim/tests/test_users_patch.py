from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_user
from authentik.lib.generators import generate_id
from authentik.sources.scim.constants import SCIM_URN_USER_ENTERPRISE
from authentik.sources.scim.models import SCIMSource, SCIMSourceUser
from authentik.sources.scim.patch.processor import SCIMPatchProcessor


class TestSCIMUsersPatch(APITestCase):
    """Test SCIM User Patch"""

    def test_add(self):
        req = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {"op": "Add", "path": "name.givenName", "value": "aqwer"},
                {"op": "Add", "path": "name.familyName", "value": "qwerqqqq"},
                {"op": "Add", "path": "name.formatted", "value": "aqwer qwerqqqq"},
            ],
        }
        user = create_test_user()
        source = SCIMSource.objects.create(slug=generate_id())
        connection = SCIMSourceUser.objects.create(
            user=user,
            id=generate_id(),
            source=source,
            attributes={
                "meta": {"resourceType": "User"},
                "active": True,
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:User",
                    SCIM_URN_USER_ENTERPRISE,
                ],
                "userName": "test@t.goauthentik.io",
                "externalId": "test",
                "displayName": "Test MS",
            },
        )
        updated = SCIMPatchProcessor().apply_patches(connection.attributes, req["Operations"])
        self.assertEqual(
            updated,
            {
                "meta": {"resourceType": "User"},
                "active": True,
                "name": {
                    "givenName": "aqwer",
                    "familyName": "qwerqqqq",
                    "formatted": "aqwer qwerqqqq",
                },
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:User",
                    SCIM_URN_USER_ENTERPRISE,
                ],
                "userName": "test@t.goauthentik.io",
                "externalId": "test",
                "displayName": "Test MS",
            },
        )

    def test_add_no_path(self):
        """Test add patch with no path set"""
        req = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {"op": "Add", "value": {"externalId": "aqwer"}},
            ],
        }
        user = create_test_user()
        source = SCIMSource.objects.create(slug=generate_id())
        connection = SCIMSourceUser.objects.create(
            user=user,
            id=generate_id(),
            source=source,
            attributes={
                "meta": {"resourceType": "User"},
                "active": True,
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:User",
                    SCIM_URN_USER_ENTERPRISE,
                ],
                "userName": "test@t.goauthentik.io",
                "displayName": "Test MS",
            },
        )
        updated = SCIMPatchProcessor().apply_patches(connection.attributes, req["Operations"])
        self.assertEqual(
            updated,
            {
                "meta": {"resourceType": "User"},
                "active": True,
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:User",
                    SCIM_URN_USER_ENTERPRISE,
                ],
                "userName": "test@t.goauthentik.io",
                "externalId": "aqwer",
                "displayName": "Test MS",
            },
        )

    def test_replace(self):
        req = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {"op": "Replace", "path": "name", "value": {"givenName": "aqwer"}},
            ],
        }
        user = create_test_user()
        source = SCIMSource.objects.create(slug=generate_id())
        connection = SCIMSourceUser.objects.create(
            user=user,
            id=generate_id(),
            source=source,
            attributes={
                "meta": {"resourceType": "User"},
                "active": True,
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:User",
                    SCIM_URN_USER_ENTERPRISE,
                ],
                "userName": "test@t.goauthentik.io",
                "externalId": "test",
                "displayName": "Test MS",
            },
        )
        updated = SCIMPatchProcessor().apply_patches(connection.attributes, req["Operations"])
        self.assertEqual(
            updated,
            {
                "meta": {"resourceType": "User"},
                "active": True,
                "name": {
                    "givenName": "aqwer",
                },
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:User",
                    SCIM_URN_USER_ENTERPRISE,
                ],
                "userName": "test@t.goauthentik.io",
                "externalId": "test",
                "displayName": "Test MS",
            },
        )

    def test_replace_no_path(self):
        """Test value replace with no path"""
        req = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {"op": "Replace", "value": {"externalId": "aqwer"}},
            ],
        }
        user = create_test_user()
        source = SCIMSource.objects.create(slug=generate_id())
        connection = SCIMSourceUser.objects.create(
            user=user,
            id=generate_id(),
            source=source,
            attributes={
                "meta": {"resourceType": "User"},
                "active": True,
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:User",
                    SCIM_URN_USER_ENTERPRISE,
                ],
                "userName": "test@t.goauthentik.io",
                "externalId": "test",
                "displayName": "Test MS",
            },
        )
        updated = SCIMPatchProcessor().apply_patches(connection.attributes, req["Operations"])
        self.assertEqual(
            updated,
            {
                "meta": {"resourceType": "User"},
                "active": True,
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:User",
                    SCIM_URN_USER_ENTERPRISE,
                ],
                "userName": "test@t.goauthentik.io",
                "externalId": "aqwer",
                "displayName": "Test MS",
            },
        )

    def test_remove(self):
        req = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {"op": "Remove", "path": "name", "value": {"givenName": "aqwer"}},
            ],
        }
        user = create_test_user()
        source = SCIMSource.objects.create(slug=generate_id())
        connection = SCIMSourceUser.objects.create(
            user=user,
            id=generate_id(),
            source=source,
            attributes={
                "meta": {"resourceType": "User"},
                "active": True,
                "name": {
                    "givenName": "aqwer",
                },
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:User",
                    SCIM_URN_USER_ENTERPRISE,
                ],
                "userName": "test@t.goauthentik.io",
                "externalId": "test",
                "displayName": "Test MS",
            },
        )
        updated = SCIMPatchProcessor().apply_patches(connection.attributes, req["Operations"])
        self.assertEqual(
            updated,
            {
                "meta": {"resourceType": "User"},
                "active": True,
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:User",
                    SCIM_URN_USER_ENTERPRISE,
                ],
                "userName": "test@t.goauthentik.io",
                "externalId": "test",
                "displayName": "Test MS",
            },
        )

    def test_large(self):
        """Large amount of patch operations"""
        req = {
            "Operations": [
                {
                    "op": "replace",
                    "path": "emails[primary eq true].value",
                    "value": "dandre_kling@wintheiser.info",
                },
                {
                    "op": "replace",
                    "path": "phoneNumbers[primary eq true].value",
                    "value": "72-634-1548",
                },
                {
                    "op": "replace",
                    "path": "phoneNumbers[primary eq true].display",
                    "value": "72-634-1548",
                },
                {"op": "replace", "path": "ims[primary eq true].value", "value": "GXSGJKWGHVVS"},
                {"op": "replace", "path": "ims[primary eq true].display", "value": "IMCHDKUQIPYB"},
                {
                    "op": "replace",
                    "path": "photos[primary eq true].display",
                    "value": "TWAWLHHSUNIV",
                },
                {
                    "op": "replace",
                    "path": "addresses[primary eq true].formatted",
                    "value": "TMINZQAJQDCL",
                },
                {
                    "op": "replace",
                    "path": "addresses[primary eq true].streetAddress",
                    "value": "081 Wisoky Key",
                },
                {
                    "op": "replace",
                    "path": "addresses[primary eq true].locality",
                    "value": "DPFASBZRPMDP",
                },
                {
                    "op": "replace",
                    "path": "addresses[primary eq true].region",
                    "value": "WHSTJSPIPTCF",
                },
                {
                    "op": "replace",
                    "path": "addresses[primary eq true].postalCode",
                    "value": "ko28 1qa",
                },
                {"op": "replace", "path": "addresses[primary eq true].country", "value": "Taiwan"},
                {
                    "op": "replace",
                    "path": "entitlements[primary eq true].value",
                    "value": "NGBJMUYZVVBX",
                },
                {"op": "replace", "path": "roles[primary eq true].value", "value": "XEELVFMMWCVM"},
                {
                    "op": "replace",
                    "path": "x509Certificates[primary eq true].value",
                    "value": "UYISMEDOXUZY",
                },
                {
                    "op": "replace",
                    "value": {
                        "externalId": "7faaefb0-0774-4d8e-8f6d-863c361bc72c",
                        "name.formatted": "Dell",
                        "name.familyName": "Gay",
                        "name.givenName": "Kyler",
                        "name.middleName": "Hannah",
                        "name.honorificPrefix": "Cassie",
                        "name.honorificSuffix": "Yolanda",
                        "displayName": "DPRLIJSFQMTL",
                        "nickName": "BKSPMIRMFBTI",
                        "title": "NBZCOAXVYJUY",
                        "userType": "ZGJMYZRUORZE",
                        "preferredLanguage": "as-IN",
                        "locale": "JLOJHLPWZODG",
                        "timezone": "America/Argentina/Rio_Gallegos",
                        "active": True,
                        f"{SCIM_URN_USER_ENTERPRISE}:employeeNumber": "PDFWRRZBQOHB",
                        f"{SCIM_URN_USER_ENTERPRISE}:costCenter": "HACMZWSEDOTQ",
                        f"{SCIM_URN_USER_ENTERPRISE}:organization": "LXVHJUOLNCLS",
                        f"{SCIM_URN_USER_ENTERPRISE}:division": "JASVTPKPBPMG",
                        f"{SCIM_URN_USER_ENTERPRISE}:department": "GMSBFLMNPABY",
                    },
                },
            ],
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
        }
        user = create_test_user()
        source = SCIMSource.objects.create(slug=generate_id())
        connection = SCIMSourceUser.objects.create(
            user=user,
            id=generate_id(),
            source=source,
            attributes={
                "active": True,
                "addresses": [
                    {
                        "primary": "true",
                        "formatted": "BLJMCNXHYLZK",
                        "streetAddress": "7801 Jacobs Fork",
                        "locality": "HZJBJWFAKXDD",
                        "region": "GJXCXPMIIKWK",
                        "postalCode": "pv82 8ua",
                        "country": "India",
                    }
                ],
                "displayName": "KEFXCHKHAFOT",
                "emails": [{"primary": "true", "value": "scot@zemlak.uk"}],
                "entitlements": [{"primary": "true", "value": "FTTUXWYDAAQC"}],
                "externalId": "448d2786-7bf6-4e03-a4ef-64cbaf162fa7",
                "ims": [{"primary": "true", "value": "IGWZUUMCMKXS", "display": "PJVGMMKYYHRU"}],
                "locale": "PJNYJHWJILTI",
                "name": {
                    "formatted": "Ladarius",
                    "familyName": "Manley",
                    "givenName": "Mazie",
                    "middleName": "Vernon",
                    "honorificPrefix": "Melyssa",
                    "honorificSuffix": "Demarcus",
                },
                "nickName": "HTPKOXMWZKHL",
                "phoneNumbers": [
                    {"primary": "true", "value": "50-608-7660", "display": "50-608-7660"}
                ],
                "photos": [{"primary": "true", "display": "KCONLNLSYTBP"}],
                "preferredLanguage": "wae",
                "profileUrl": "HPSEOIPXMGOH",
                "roles": [{"primary": "true", "value": "TLGYITOIZGKP"}],
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:User",
                    SCIM_URN_USER_ENTERPRISE,
                ],
                "timezone": "America/Indiana/Petersburg",
                "title": "EJWFXLHNHMCD",
                SCIM_URN_USER_ENTERPRISE: {
                    "employeeNumber": "XHDMEJUURJNR",
                    "costCenter": "RXUYBXOTRCZH",
                    "organization": "CEXWXMBRYAHN",
                    "division": "XMPFMDCLRKCW",
                    "department": "BKMNJVMCJUYS",
                    "manager": "PNGSGXLYVWMV",
                },
                "userName": "imelda.auer@kshlerin.co.uk",
                "userType": "PZFXORVSUAPU",
                "x509Certificates": [{"primary": "true", "value": "KOVKWGIVVEHH"}],
            },
        )
        updated = SCIMPatchProcessor().apply_patches(connection.attributes, req["Operations"])
        self.assertEqual(
            updated,
            {
                "active": True,
                "addresses": [
                    {
                        "primary": "true",
                        "formatted": "BLJMCNXHYLZK",
                        "streetAddress": "7801 Jacobs Fork",
                        "locality": "HZJBJWFAKXDD",
                        "region": "GJXCXPMIIKWK",
                        "postalCode": "pv82 8ua",
                        "country": "India",
                    }
                ],
                "displayName": "DPRLIJSFQMTL",
                "emails": [{"primary": "true", "value": "scot@zemlak.uk"}],
                "entitlements": [{"primary": "true", "value": "FTTUXWYDAAQC"}],
                "externalId": "7faaefb0-0774-4d8e-8f6d-863c361bc72c",
                "ims": [{"primary": "true", "value": "IGWZUUMCMKXS", "display": "PJVGMMKYYHRU"}],
                "locale": "JLOJHLPWZODG",
                "name": {
                    "formatted": "Dell",
                    "familyName": "Gay",
                    "givenName": "Kyler",
                    "middleName": "Hannah",
                    "honorificPrefix": "Cassie",
                    "honorificSuffix": "Yolanda",
                },
                "nickName": "BKSPMIRMFBTI",
                "phoneNumbers": [
                    {"primary": "true", "value": "50-608-7660", "display": "50-608-7660"}
                ],
                "photos": [{"primary": "true", "display": "KCONLNLSYTBP"}],
                "preferredLanguage": "as-IN",
                "profileUrl": "HPSEOIPXMGOH",
                "roles": [{"primary": "true", "value": "TLGYITOIZGKP"}],
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:User",
                    SCIM_URN_USER_ENTERPRISE,
                ],
                "timezone": "America/Argentina/Rio_Gallegos",
                "title": "NBZCOAXVYJUY",
                SCIM_URN_USER_ENTERPRISE: {
                    "employeeNumber": "PDFWRRZBQOHB",
                    "costCenter": "HACMZWSEDOTQ",
                    "organization": "LXVHJUOLNCLS",
                    "division": "JASVTPKPBPMG",
                    "department": "GMSBFLMNPABY",
                    "manager": "PNGSGXLYVWMV",
                },
                "userName": "imelda.auer@kshlerin.co.uk",
                "userType": "ZGJMYZRUORZE",
                "x509Certificates": [{"primary": "true", "value": "KOVKWGIVVEHH"}],
            },
        )

    def test_schema_urn_manager(self):
        req = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "Add",
                    "value": {
                        "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User:manager": "foo"
                    },
                },
            ],
        }
        user = create_test_user()
        source = SCIMSource.objects.create(slug=generate_id())
        connection = SCIMSourceUser.objects.create(
            user=user,
            id=generate_id(),
            source=source,
            attributes={
                "meta": {"resourceType": "User"},
                "active": True,
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:User",
                    SCIM_URN_USER_ENTERPRISE,
                ],
                "userName": "test@t.goauthentik.io",
                "externalId": "test",
                "displayName": "Test MS",
            },
        )
        updated = SCIMPatchProcessor().apply_patches(connection.attributes, req["Operations"])
        self.assertEqual(
            updated,
            {
                "meta": {"resourceType": "User"},
                "active": True,
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:User",
                    SCIM_URN_USER_ENTERPRISE,
                ],
                "userName": "test@t.goauthentik.io",
                "externalId": "test",
                "displayName": "Test MS",
                "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User": {
                    "manager": {"value": "foo"}
                },
            },
        )
