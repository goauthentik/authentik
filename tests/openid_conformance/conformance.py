#!/usr/bin/env python3
#
# python wrapper for conformance suite API


import asyncio
import json
import os
import re
import time
import traceback
import zipfile

import httpx


class RetryTransport(httpx.HTTPTransport):
    def handle_request(
        self,
        request: httpx.Request,
    ) -> httpx.Response:
        retry = 0
        resp = None
        while retry < 5:
            retry += 1
            if retry > 2:
                time.sleep(1)
            try:
                if resp is not None:
                    resp.close()
                resp = super().handle_request(request)
            except Exception as e:
                print(f"httpx {request.url} exception {e} caught - retrying")
                continue
            if resp.status_code >= 500 and resp.status_code < 600:
                print(f"httpx {request.url} 5xx response - retrying")
                continue
            content_type = resp.headers.get("Content-Type")
            if content_type is not None:
                mime_type, _, _ = content_type.partition(";")
                if mime_type == "application/json":
                    try:
                        resp.read()
                        resp.json()
                    except Exception as e:
                        traceback.print_exc()
                        print(
                            f"httpx {request.url} response not decodable as json '{e}' - retrying"
                        )
                        continue
            break
        return resp


class Conformance:
    def __init__(self, api_url_base, api_token, verify_ssl):
        if not api_url_base.endswith("/"):
            api_url_base += "/"
        self.api_url_base = api_url_base
        transport = RetryTransport(verify=verify_ssl)
        self.httpclient = httpx.Client(verify=verify_ssl, transport=transport, timeout=20)
        headers = {"Content-Type": "application/json"}
        if api_token is not None:
            headers["Authorization"] = f"Bearer {api_token}"
        self.httpclient.headers = headers

    async def get_all_test_modules(self):
        """Returns an array containing a dictionary per test module"""
        api_url = f"{self.api_url_base}api/runner/available"
        response = self.httpclient.get(api_url)

        if response.status_code != 200:
            raise Exception(
                f"get_all_test_modules failed - HTTP {response.status_code:d} {response.content}"
            )
        return response.json()

    def get_test_status(self,module_id):
        """Returns an array containing a dictionary per test module"""
        api_url = f"{self.api_url_base}api/runner/{module_id}"
        response = self.httpclient.get(api_url)

        if response.status_code != 200:
            raise Exception(
                f"get_test_status failed - HTTP {response.status_code:d} {response.content}"
            )
        return response.json()

    async def exporthtml(self, plan_id, path):
        for i in range(5):
            api_url = f"{self.api_url_base}api/plan/exporthtml/{plan_id}"
            try:
                with self.httpclient.stream("GET", api_url) as response:
                    if response.status_code != 200:
                        raise Exception(
                            f"exporthtml failed - HTTP {response.status_code:d} {response.content}"
                        )
                    d = response.headers["content-disposition"]
                    local_filename = re.findall('filename="(.+)"', d)[0]
                    full_path = os.path.join(path, local_filename)
                    with open(full_path, "wb") as f:
                        for chunk in response.iter_bytes():
                            f.write(chunk)
                zip_file = zipfile.ZipFile(full_path)
                ret = zip_file.testzip()
                if ret is not None:
                    raise Exception(
                        f"exporthtml for {plan_id} downloaded corrupt zip file {full_path} - {str(ret)}"
                    )
                return full_path
            except Exception as e:
                print(f"httpx {api_url} exception {e} caught - retrying")
                await asyncio.sleep(1)
        raise Exception(f"exporthtml for {plan_id} failed even after retries")

    async def create_certification_package(
        self, plan_id, conformance_pdf_path, rp_logs_zip_path=None, output_zip_directory="./"
    ):
        """
        Create a complete certification package zip file which is written
        to the directory specified by the 'output_zip_directory' parameter.
        Calling this function will additionally publish and mark the test plan as immutable.

        :param plan_id:         The plan id for which to create the package.
        :conformance_pdf_path:  The path to the signed Certification of Conformance PDF document.
        :rp_logs_zip_path:      Required for RP tests and is the path to the client logs zip file.
        :output_zip_directory:  The (already existing) directory to which the certification package zip file is written.
        """
        certificationOfConformancePdf = open(conformance_pdf_path, "rb")
        clientSideData = (
            open(rp_logs_zip_path, "rb") if rp_logs_zip_path is not None else open(os.devnull, "rb")
        )
        files = {
            "certificationOfConformancePdf": certificationOfConformancePdf,
            "clientSideData": clientSideData,
        }
        try:
            with httpx.Client() as multipartClient:
                multipartClient.headers = self.httpclient.headers.copy()
                multipartClient.headers.pop("content-type")
                api_url = f"{self.api_url_base}api/plan/{plan_id}/certificationpackage"

                response = multipartClient.post(api_url, files=files)
                if response.status_code != 200:
                    raise Exception(
                        f"certificationpackage failed - HTTP {response.status_code:d} {response.content}"
                    )

                d = response.headers["content-disposition"]
                local_filename = re.findall('filename="(.+)"', d)[0]
                full_path = os.path.join(output_zip_directory, local_filename)
                with open(full_path, "wb") as f:
                    for chunk in response.iter_bytes():
                        f.write(chunk)
                print(
                    f"Certification package zip for plan id {plan_id} written to {full_path}"
                )
        finally:
            certificationOfConformancePdf.close()
            clientSideData.close()

    def create_test_plan(self, name, configuration, variant=None):
        api_url = f"{self.api_url_base}api/plan"
        payload = {"planName": name}
        if variant != None:
            payload["variant"] = json.dumps(variant)
        response = self.httpclient.post(api_url, params=payload, data=configuration)

        if response.status_code != 201:
            raise Exception(
                f"create_test_plan failed - HTTP {response.status_code:d} {response.content}"
            )
        return response.json()

    def create_test(self, test_name, configuration):
        api_url = f"{self.api_url_base}api/runner"
        payload = {"test": test_name}
        response = self.httpclient.post(api_url, params=payload, data=configuration)

        if response.status_code != 201:
            raise Exception(
                f"create_test failed - HTTP {response.status_code:d} {response.content}"
            )
        return response.json()

    async def create_test_from_plan(self, plan_id, test_name):
        api_url = f"{self.api_url_base}api/runner"
        payload = {"test": test_name, "plan": plan_id}
        response = self.httpclient.post(api_url, params=payload)

        if response.status_code != 201:
            raise Exception(
                f"create_test_from_plan failed - HTTP {response.status_code:d} {response.content}"
            )
        return response.json()

    def create_test_from_plan_with_variant(self, plan_id, test_name, variant):
        api_url = f"{self.api_url_base}api/runner"
        payload = {"test": test_name, "plan": plan_id}
        if variant != None:
            payload["variant"] = json.dumps(variant)
        response = self.httpclient.post(api_url, params=payload)

        if response.status_code != 201:
            raise Exception(
                f"create_test_from_plan failed - HTTP {response.status_code:d} {response.content}"
            )
        return response.json()

    def get_module_info(self, module_id):
        api_url = f"{self.api_url_base}api/info/{module_id}"
        response = self.httpclient.get(api_url)

        if response.status_code != 200:
            raise Exception(
                f"get_module_info failed - HTTP {response.status_code:d} {response.content}"
            )
        return response.json()

    def get_test_log(self, module_id):
        api_url = f"{self.api_url_base}api/log/{module_id}"
        response = self.httpclient.get(api_url)

        if response.status_code != 200:
            raise Exception(
                f"get_test_log failed - HTTP {response.status_code:d} {response.content}"
            )
        return response.json()

    def upload_image(self, log_id, placeholder, data):
        api_url = f"{self.api_url_base}api/log/{log_id}/images/{placeholder}"
        response = self.httpclient.post(api_url, data=data, headers={
            "Content-Type": "text/plain"
        })

        if response.status_code != 200:
            raise Exception(
                f"upload_image failed - HTTP {response.status_code:d} {response.content}"
            )
        return response.json()

    async def start_test(self, module_id):
        api_url = f"{self.api_url_base}api/runner/{module_id}"
        response = self.httpclient.post(api_url)

        if response.status_code != 200:
            raise Exception(
                f"start_test failed - HTTP {response.status_code:d} {response.content}"
            )
        return response.json()

    def wait_for_state(self, module_id, required_states, timeout=240):
        timeout_at = time.time() + timeout
        while True:
            if time.time() > timeout_at:
                raise Exception(
                    f"Timed out waiting for test module {module_id} to be in one of states: {required_states}"
                )

            info = self.get_module_info(module_id)

            status = info["status"]
            print(f"module id {module_id} status is {status}")
            if status in required_states:
                return status
            if status == "INTERRUPTED":
                raise Exception(f"Test module {module_id} has moved to INTERRUPTED")

            time.sleep(1)

    async def close_client(self):
        self.httpclient.close()
