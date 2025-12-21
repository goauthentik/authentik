import json
import os
import re
import time
import zipfile

from requests import RequestException
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from authentik.lib.utils.http import get_http_session


class Conformance:
    HTTP_OK = 200
    HTTP_CREATED = 201

    def __init__(self, api_url_base, api_token, verify_ssl):
        if not api_url_base.endswith("/"):
            api_url_base += "/"
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

    def get_all_test_modules(self):
        url = f"{self.api_url_base}api/runner/available"
        response = self.session.get(url)
        if response.status_code != Conformance.HTTP_OK:
            raise Exception(
                f"get_all_test_modules failed - HTTP {response.status_code} {response.content}"
            )
        return response.json()

    def get_test_status(self, module_id):
        url = f"{self.api_url_base}api/runner/{module_id}"
        response = self.session.get(url)
        if response.status_code != Conformance.HTTP_OK:
            raise Exception(
                f"get_test_status failed - HTTP {response.status_code} {response.content}"
            )
        return response.json()

    def exporthtml(self, plan_id, path):
        for _ in range(5):
            url = f"{self.api_url_base}api/plan/exporthtml/{plan_id}"
            try:
                with self.session.get(url, stream=True) as response:
                    if response.status_code != Conformance.HTTP_OK:
                        raise Exception(
                            f"exporthtml failed - HTTP {response.status_code} {response.content}"
                        )
                    cd = response.headers.get("content-disposition", "")
                    local_filename = re.findall('filename="(.+)"', cd)[0]
                    full_path = os.path.join(path, local_filename)
                    with open(full_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                zip_file = zipfile.ZipFile(full_path)
                ret = zip_file.testzip()
                if ret is not None:
                    raise Exception(f"exporthtml returned corrupt zip file: {ret}")
                return full_path
            except RequestException as e:
                print(f"requests {url} exception {e} caught - retrying")
                time.sleep(1)
        raise Exception(f"exporthtml for {plan_id} failed even after retries")

    def create_certification_package(
        self, plan_id, conformance_pdf_path, rp_logs_zip_path=None, output_zip_directory="./"
    ):
        with (
            open(conformance_pdf_path, "rb") as cert_pdf,
            open(rp_logs_zip_path, "rb") if rp_logs_zip_path else open(os.devnull, "rb") as rp_logs,
        ):
            files = {
                "certificationOfConformancePdf": cert_pdf,
                "clientSideData": rp_logs,
            }

            headers = self.session.headers.copy()
            headers.pop("Content-Type", None)

            url = f"{self.api_url_base}api/plan/{plan_id}/certificationpackage"
            response = self.session.post(url, files=files, headers=headers)
            if response.status_code != Conformance.HTTP_OK:
                raise Exception(
                    f"certificationpackage failed - HTTP {response.status_code} {response.content}"
                )

            cd = response.headers.get("content-disposition", "")
            local_filename = re.findall('filename="(.+)"', cd)[0]
            full_path = os.path.join(output_zip_directory, local_filename)
            with open(full_path, "wb") as f:
                f.write(response.content)
            print(f"Certification package zip for plan id {plan_id} written to {full_path}")

    def create_test_plan(self, name, configuration, variant=None):
        url = f"{self.api_url_base}api/plan"
        payload = {"planName": name}
        if variant is not None:
            payload["variant"] = json.dumps(variant)
        response = self.session.post(url, params=payload, data=configuration)
        if response.status_code != Conformance.HTTP_CREATED:
            raise Exception(
                f"create_test_plan failed - HTTP {response.status_code} {response.content}"
            )
        return response.json()

    def create_test(self, test_name, configuration):
        url = f"{self.api_url_base}api/runner"
        payload = {"test": test_name}
        response = self.session.post(url, params=payload, data=configuration)
        if response.status_code != Conformance.HTTP_CREATED:
            raise Exception(f"create_test failed - HTTP {response.status_code} {response.content}")
        return response.json()

    def create_test_from_plan(self, plan_id, test_name):
        url = f"{self.api_url_base}api/runner"
        payload = {"test": test_name, "plan": plan_id}
        response = self.session.post(url, params=payload)
        if response.status_code != Conformance.HTTP_CREATED:
            raise Exception(
                f"create_test_from_plan failed - HTTP {response.status_code} {response.content}"
            )
        return response.json()

    def create_test_from_plan_with_variant(self, plan_id, test_name, variant):
        url = f"{self.api_url_base}api/runner"
        payload = {"test": test_name, "plan": plan_id}
        if variant is not None:
            payload["variant"] = json.dumps(variant)
        response = self.session.post(url, params=payload)
        if response.status_code != Conformance.HTTP_CREATED:
            raise Exception(
                "create_test_from_plan_with_variant failed - "
                f"HTTP {response.status_code} {response.content}"
            )
        return response.json()

    def get_module_info(self, module_id):
        url = f"{self.api_url_base}api/info/{module_id}"
        response = self.session.get(url)
        if response.status_code != Conformance.HTTP_OK:
            raise Exception(
                f"get_module_info failed - HTTP {response.status_code} {response.content}"
            )
        return response.json()

    def get_test_log(self, module_id):
        url = f"{self.api_url_base}api/log/{module_id}"
        response = self.session.get(url)
        if response.status_code != Conformance.HTTP_OK:
            raise Exception(f"get_test_log failed - HTTP {response.status_code} {response.content}")
        return response.json()

    def upload_image(self, log_id, placeholder, data):
        url = f"{self.api_url_base}api/log/{log_id}/images/{placeholder}"
        response = self.session.post(url, data=data, headers={"Content-Type": "text/plain"})
        if response.status_code != Conformance.HTTP_OK:
            raise Exception(f"upload_image failed - HTTP {response.status_code} {response.content}")

    def start_test(self, module_id):
        url = f"{self.api_url_base}api/runner/{module_id}"
        response = self.session.post(url)
        if response.status_code != Conformance.HTTP_OK:
            raise Exception(f"start_test failed - HTTP {response.status_code} {response.content}")
        return response.json()

    def wait_for_state(self, module_id, required_states, timeout=240):
        timeout_at = time.time() + timeout
        while time.time() < timeout_at:
            info = self.get_module_info(module_id)
            status = info.get("status")
            if status in required_states:
                return status
            if status == "INTERRUPTED":
                raise Exception(f"Test module {module_id} has moved to INTERRUPTED")
            time.sleep(1)
        raise Exception(
            f"Timed out waiting for test module {module_id} "
            f"to be in one of states: {required_states}"
        )
