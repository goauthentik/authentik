import re
import zipfile
from json import dumps
from os import devnull
from pathlib import Path
from time import sleep, time
from typing import Any, cast

from requests import RequestException
from requests.adapters import HTTPAdapter
from requests.sessions import default_headers
from urllib3.util.retry import Retry

from authentik.lib.utils.http import get_http_session


class ConformanceException(Exception):
    """Exception in conformance testing"""


class Conformance:
    HTTP_OK = 200
    HTTP_CREATED = 201

    def __init__(self, api_url_base: str, api_token: str | None, verify_ssl: bool):
        self.api_url_base = api_url_base
        self.session = get_http_session()
        self.session.verify = verify_ssl
        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.session.mount("http://", HTTPAdapter(max_retries=retries))

        self.session.headers.update({"Content-Type": "application/json"})
        if api_token is not None:
            self.session.headers.update({"Authorization": f"Bearer {api_token}"})

    def get_all_test_modules(self) -> list[dict[str, Any]]:
        url = f"{self.api_url_base}/api/runner/available"
        response = self.session.get(url)
        if response.status_code != Conformance.HTTP_OK:
            raise ConformanceException(
                f"get_all_test_modules failed - HTTP {response.status_code} {response.text}"
            )
        return cast(list[dict[str, Any]], response.json())

    def get_test_status(self, module_id: str) -> dict[str, Any]:
        url = f"{self.api_url_base}/api/runner/{module_id}"
        response = self.session.get(url)
        if response.status_code != Conformance.HTTP_OK:
            raise ConformanceException(
                f"get_test_status failed - HTTP {response.status_code} {response.text}"
            )
        return cast(dict[str, Any], response.json())

    def export_html(self, plan_id: str, path: Path | str) -> Path:
        for _ in range(5):
            url = f"{self.api_url_base}/api/plan/exporthtml/{plan_id}"
            try:
                with self.session.get(url, stream=True) as response:
                    if response.status_code != Conformance.HTTP_OK:
                        raise ConformanceException(
                            f"exporthtml failed - HTTP {response.status_code} {response.text}"
                        )
                    cd = response.headers.get("content-disposition", "")
                    local_filename = Path(re.findall('filename="(.+)"', cd)[0])
                    full_path = Path(path) / local_filename
                    with open(full_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                zip_file = zipfile.ZipFile(full_path)
                ret = zip_file.testzip()
                if ret is not None:
                    raise ConformanceException(f"export_html returned corrupt zip file: {ret}")
                return full_path
            except RequestException as e:
                print(f"requests {url} exception {e} caught - retrying")
                sleep(1)
        raise ConformanceException(f"export_html for {plan_id} failed even after retries")

    def create_certification_package(
        self,
        plan_id: str,
        conformance_pdf_path: Path | str,
        rp_logs_zip_path: Path | str | None = None,
        output_zip_directory: Path | str = "./",
    ) -> None:
        with (
            open(conformance_pdf_path, "rb") as cert_pdf,
            open(rp_logs_zip_path, "rb") if rp_logs_zip_path else open(devnull, "rb") as rp_logs,
        ):
            files = {
                "certificationOfConformancePdf": cert_pdf,
                "clientSideData": rp_logs,
            }

            headers = default_headers()
            headers.pop("Content-Type", None)

            url = f"{self.api_url_base}/api/plan/{plan_id}/certificationpackage"
            response = self.session.post(url, files=files, headers=headers)
            if response.status_code != Conformance.HTTP_OK:
                raise ConformanceException(
                    f"certificationpackage failed - HTTP {response.status_code} {response.text}"
                )

            cd = response.headers.get("content-disposition", "")
            local_filename = Path(re.findall('filename="(.+)"', cd)[0])
            full_path = Path(output_zip_directory) / local_filename
            with open(full_path, "wb") as f:
                f.write(response.content)
            print(f"Certification package zip for plan id {plan_id} written to {full_path}")

    def create_test_plan(
        self, name: str, configuration: dict[str, Any], variant: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        url = f"{self.api_url_base}/api/plan"
        payload = {"planName": name}
        if variant is not None:
            payload["variant"] = dumps(variant)
        response = self.session.post(url, params=payload, data=dumps(configuration))
        if response.status_code != Conformance.HTTP_CREATED:
            raise ConformanceException(
                f"create_test_plan failed - HTTP {response.status_code} {response.text}"
            )
        return cast(dict[str, Any], response.json())

    def create_test(self, test_name: str, configuration: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.api_url_base}/api/runner"
        payload = {"test": test_name}
        response = self.session.post(url, params=payload, data=dumps(configuration))
        if response.status_code != Conformance.HTTP_CREATED:
            raise ConformanceException(
                f"create_test failed - HTTP {response.status_code} {response.text}"
            )
        return cast(dict[str, Any], response.json())

    def create_test_from_plan(self, plan_id: str, test_name: str) -> dict[str, Any]:
        url = f"{self.api_url_base}/api/runner"
        payload = {"test": test_name, "plan": plan_id}
        response = self.session.post(url, params=payload)
        if response.status_code != Conformance.HTTP_CREATED:
            raise ConformanceException(
                f"create_test_from_plan failed - HTTP {response.status_code} {response.text}"
            )
        return cast(dict[str, Any], response.json())

    def create_test_from_plan_with_variant(
        self, plan_id: str, test_name: str, variant: dict[str, Any]
    ) -> dict[str, Any]:
        url = f"{self.api_url_base}/api/runner"
        payload = {"test": test_name, "plan": plan_id}
        if variant is not None:
            payload["variant"] = dumps(variant)
        response = self.session.post(url, params=payload)
        if response.status_code != Conformance.HTTP_CREATED:
            raise ConformanceException(
                "create_test_from_plan_with_variant failed - "
                f"HTTP {response.status_code} {response.text}"
            )
        return cast(dict[str, Any], response.json())

    def get_module_info(self, module_id: str) -> dict[str, Any]:
        url = f"{self.api_url_base}/api/info/{module_id}"
        response = self.session.get(url)
        if response.status_code != Conformance.HTTP_OK:
            raise ConformanceException(
                f"get_module_info failed - HTTP {response.status_code} {response.text}"
            )
        return cast(dict[str, Any], response.json())

    def get_test_log(self, module_id: str) -> list[dict[str, Any]]:
        url = f"{self.api_url_base}/api/log/{module_id}"
        response = self.session.get(url)
        if response.status_code != Conformance.HTTP_OK:
            raise ConformanceException(
                f"get_test_log failed - HTTP {response.status_code} {response.text}"
            )
        return cast(list[dict[str, Any]], response.json())

    def upload_image(self, log_id: str, placeholder: str, data: Any) -> None:
        url = f"{self.api_url_base}/api/log/{log_id}/images/{placeholder}"
        response = self.session.post(url, data=data, headers={"Content-Type": "text/plain"})
        if response.status_code != Conformance.HTTP_OK:
            raise ConformanceException(
                f"upload_image failed - HTTP {response.status_code} {response.text}"
            )

    def start_test(self, module_id: str) -> dict[str, Any]:
        url = f"{self.api_url_base}/api/runner/{module_id}"
        response = self.session.post(url)
        if response.status_code != Conformance.HTTP_OK:
            raise ConformanceException(
                f"start_test failed - HTTP {response.status_code} {response.text}"
            )
        return cast(dict[str, Any], response.json())

    def wait_for_state(self, module_id: str, required_states: list[str], timeout: int = 240) -> str:
        timeout_at = time() + timeout
        while time() < timeout_at:
            info = self.get_module_info(module_id)
            status: str | None = info.get("status")
            if status in required_states:
                return status
            if status == "INTERRUPTED":
                raise ConformanceException(f"Test module {module_id} has moved to INTERRUPTED")
            sleep(1)
        raise ConformanceException(
            f"Timed out waiting for test module {module_id} "
            f"to be in one of states: {required_states}"
        )
