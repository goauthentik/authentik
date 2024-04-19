import http from "k6/http";
import { check, fail } from "k6";

const host = __ENV.BENCH_HOST ? __ENV.BENCH_HOST : "localhost";
const VUs = __ENV.VUS ? __ENV.VUS : 8;

export const options = {
    scenarios: Object.fromEntries(
        ["no-mfa", "with-mfa"].map((obj, i) => [
            obj,
            {
                executor: "constant-vus",
                vus: VUs,
                duration: "150s",
                startTime: `${165 * i}s`,
                env: {
                    DOMAIN: `login-${obj}`,
                },
                tags: {
                    testid: `login-${obj}`,
                },
            },
        ]),
    ),
};

export default function () {
    const domain = __ENV.DOMAIN;
    const url = http.url`http://${domain}.${host}:9000/api/v3/flows/executor/default-authentication-flow/`;
    const cookieJar = new http.CookieJar();
    const params = {
        jar: cookieJar,
        headers: {
            "Content-Type": "application/json",
            Accept: "*/*",
        },
    };
    let res = http.get(url, params);
    let i = 0;
    while (true) {
        if (i > 10) {
            fail("Test made more than 10 queries.");
            break;
        }
        check(res, {
            "status is 200": (res) => res.status === 200,
        });
        if (res.status !== 200) {
            fail("Endpoint did not return 200.");
            break;
        }

        const component = res.json()["component"];
        let payload = {};
        if (component === "ak-stage-identification") {
            payload = {
                uid_field: "test",
            };
        } else if (component === "ak-stage-password") {
            payload = {
                password: "verySecurePassword",
            };
        } else if (component === "ak-stage-authenticator-validate") {
            payload = {
                code: "staticToken",
            };
        } else if (component === "xak-flow-redirect") {
            break;
        } else {
            console.log(`Unknown component type: ${component}`);
            break;
        }

        payload["component"] = component;
        res = http.post(url, JSON.stringify(payload), params);
        i++;
    }
}
