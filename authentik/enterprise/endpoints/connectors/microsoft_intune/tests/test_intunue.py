from json import loads
from unittest.mock import MagicMock, patch

from kiota_serialization_json.json_parse_node import JsonParseNode
from msgraph.generated.models.managed_device import ManagedDevice
from rest_framework.test import APITestCase

from authentik.endpoints.facts import DeviceFacts, OSFamily
from authentik.enterprise.endpoints.connectors.microsoft_intune.controller import (
    MicrosoftIntuneController,
)
from authentik.enterprise.endpoints.connectors.microsoft_intune.models import (
    MicrosoftIntuneConnector,
)
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture

TEST_HOST = loads(load_fixture("fixtures/device.json"))


class TestIntuneConnector(APITestCase):
    def setUp(self):
        self.connector = MicrosoftIntuneConnector.objects.create(
            name=generate_id(),
            client_id=generate_id(),
            client_secret=generate_id(),
            tenant_id=generate_id(),
        )

    @patch(
        "authentik.enterprise.endpoints.connectors.microsoft_intune.models.MicrosoftIntuneConnector.microsoft_credentials",
        MagicMock(return_value={}),
    )
    def test_map_single(self):
        parse_node = JsonParseNode(TEST_HOST["value"][0])
        device = parse_node.get_object_value(ManagedDevice)
        ctrl = MicrosoftIntuneController(self.connector)
        mapped = ctrl.map_device_data(device)
        DeviceFacts(data=mapped).is_valid(raise_exception=True)
        self.assertEqual(
            mapped,
            {
                "disks": [
                    {
                        "encryption_enabled": True,
                        "mountpoint": "/",
                        "name": "virtual@intune.microsoft.com",
                    }
                ],
                "hardware": {
                    "manufacturer": "Manufacturer value",
                    "memory_bytes": 5,
                    "model": "Model value",
                    "serial": "Serial Number value",
                },
                "network": {"hostname": "Device Name value", "interfaces": []},
                "os": {
                    "family": OSFamily.other,
                    "name": "Operating System value",
                    "version": "Os Version value",
                },
                "software": [],
                "vendor": {
                    "intune.microsoft.com": {
                        "activation_lock_bypass_code": "Activation Lock Bypass Code value",
                        "additional_data": {},
                        "android_security_patch_level": "Android Security Patch Level value",
                        "azure_a_d_device_id": "Azure ADDevice Id value",
                        "azure_a_d_registered": True,
                        "compliance_grace_period_expiration_date_time": (
                            "2016-12-31T23:56:44.951111-08:00"
                        ),
                        "compliance_state": "compliant",
                        "configuration_manager_client_enabled_features": {
                            "additional_data": {},
                            "compliance_policy": True,
                            "device_configuration": True,
                            "inventory": True,
                            "modern_apps": True,
                            "odata_type": (
                                "microsoft.graph.configurationManagerClientEnabledFeatures"
                            ),
                            "resource_access": True,
                            "windows_update_for_business": True,
                        },
                        "device_action_results": [
                            {
                                "action_name": "Action Name value",
                                "action_state": "pending",
                                "additional_data": {},
                                "last_updated_date_time": "2017-01-01T00:00:56.832155-08:00",
                                "odata_type": "microsoft.graph.deviceActionResult",
                                "start_date_time": "2016-12-31T23:58:46.715618-08:00",
                            }
                        ],
                        "device_category": None,
                        "device_category_display_name": "Device Category Display Name value",
                        "device_compliance_policy_states": None,
                        "device_configuration_states": None,
                        "device_enrollment_type": "userEnrollment",
                        "device_health_attestation_state": {
                            "additional_data": {},
                            "attestation_identity_key": "Attestation Identity Key value",
                            "bit_locker_status": "Bit Locker Status value",
                            "boot_app_security_version": "Boot App Security Version value",
                            "boot_debugging": "Boot Debugging value",
                            "boot_manager_security_version": "Boot Manager Security Version value",
                            "boot_manager_version": "Boot Manager Version value",
                            "boot_revision_list_info": "Boot Revision List Info value",
                            "code_integrity": "Code Integrity value",
                            "code_integrity_check_version": "Code Integrity Check Version value",
                            "code_integrity_policy": "Code Integrity Policy value",
                            "content_namespace_url": "https://example.com/contentNamespaceUrl/",
                            "content_version": "Content Version value",
                            "data_excution_policy": "Data Excution Policy value",
                            "device_health_attestation_status": (
                                "Device Health Attestation Status value"
                            ),
                            "early_launch_anti_malware_driver_protection": (
                                "Early Launch Anti Malware Driver Protection value"
                            ),
                            "health_attestation_supported_status": (
                                "Health Attestation Supported Status value"
                            ),
                            "health_status_mismatch_info": "Health Status Mismatch Info value",
                            "issued_date_time": "2016-12-31T23:58:22.123103-08:00",
                            "last_update_date_time": "Last Update Date Time value",
                            "odata_type": "microsoft.graph.deviceHealthAttestationState",
                            "operating_system_kernel_debugging": (
                                "Operating System Kernel Debugging value"
                            ),
                            "operating_system_rev_list_info": (
                                "Operating System Rev List Info value"
                            ),
                            "pcr0": "Pcr0 value",
                            "pcr_hash_algorithm": "Pcr Hash Algorithm value",
                            "reset_count": 10,
                            "restart_count": 12,
                            "safe_mode": "Safe Mode value",
                            "secure_boot": "Secure Boot value",
                            "secure_boot_configuration_policy_finger_print": (
                                "Secure Boot Configuration Policy Finger Print value"
                            ),
                            "test_signing": "Test Signing value",
                            "tpm_version": "Tpm Version value",
                            "virtual_secure_mode": "Virtual Secure Mode value",
                            "windows_p_e": "Windows PE value",
                        },
                        "device_name": "Device Name value",
                        "device_registration_state": "registered",
                        "eas_activated": True,
                        "eas_activation_date_time": "2016-12-31T23:59:43.487878-08:00",
                        "eas_device_id": "Eas Device Id value",
                        "email_address": "Email Address value",
                        "enrolled_date_time": "2016-12-31T23:59:43.797191-08:00",
                        "enrollment_profile_name": "Enrollment Profile Name value",
                        "ethernet_mac_address": "Ethernet Mac Address value",
                        "exchange_access_state": "unknown",
                        "exchange_access_state_reason": "unknown",
                        "exchange_last_successful_sync_date_time": (
                            "2017-01-01T00:00:45.880308-08:00"
                        ),
                        "free_storage_space_in_bytes": 7,
                        "iccid": "Iccid value",
                        "id": "705c034c-034c-705c-4c03-5c704c035c70",
                        "imei": "Imei value",
                        "is_encrypted": True,
                        "is_supervised": True,
                        "jail_broken": "Jail Broken value",
                        "last_sync_date_time": "2017-01-01T00:02:49.320597-08:00",
                        "log_collection_requests": None,
                        "managed_device_name": "Managed Device Name value",
                        "managed_device_owner_type": "company",
                        "management_agent": "mdm",
                        "management_certificate_expiration_date": (
                            "2016-12-31T23:57:59.978965-08:00"
                        ),
                        "management_state": "retirePending",
                        "manufacturer": "Manufacturer value",
                        "meid": "Meid value",
                        "model": "Model value",
                        "notes": "Notes value",
                        "odata_type": "#microsoft.graph.managedDevice",
                        "operating_system": "Operating System value",
                        "os_version": "Os Version value",
                        "partner_reported_threat_state": "activated",
                        "phone_number": "Phone Number value",
                        "physical_memory_in_bytes": 5,
                        "remote_assistance_session_error_details": (
                            "Remote Assistance Session Error Details value"
                        ),
                        "remote_assistance_session_url": "https://example.com/remoteAssistanceSessionUrl/",
                        "require_user_enrollment_approval": True,
                        "serial_number": "Serial Number value",
                        "subscriber_carrier": "Subscriber Carrier value",
                        "total_storage_space_in_bytes": 8,
                        "udid": "Udid value",
                        "user_display_name": "User Display Name value",
                        "user_id": "User Id value",
                        "user_principal_name": "User Principal Name value",
                        "users": None,
                        "wi_fi_mac_address": "Wi Fi Mac Address value",
                        "windows_protection_state": None,
                    }
                },
            },
        )
