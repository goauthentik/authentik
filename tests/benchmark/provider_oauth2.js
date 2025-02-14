import crypto from "k6/crypto";
import exec from "k6/execution";
import http from "k6/http";
import { check, fail } from "k6";

const host = __ENV.BENCH_HOST ? __ENV.BENCH_HOST : "localhost";
const VUs = __ENV.VUS ? __ENV.VUS : 8;

const testcases = [
    [2, 50, 2],
    [0, 0, 0],
    [10, 0, 0],
    [100, 0, 0],
    [0, 10, 0],
    [0, 100, 0],
    [0, 0, 10],
    [0, 0, 100],
    [10, 10, 10],
    [100, 100, 100],
];

export const options = {
    setupTimeout: "10m",
    scenarios: Object.fromEntries(
        testcases.map((obj, i) => [
            `${obj[0]}_${obj[1]}_${obj[2]}`,
            {
                executor: "constant-vus",
                vus: VUs,
                duration: "150s",
                startTime: `${165 * i}s`,
                env: {
                    USER_POLICIES_COUNT: `${obj[0]}`,
                    GROUP_POLICIES_COUNT: `${obj[1]}`,
                    EXPRESSION_POLICIES_COUNT: `${obj[2]}`,
                },
                tags: {
                    testid: `provider-oauth2-${obj[0]}_${obj[1]}_${obj[2]}`,
                    user_policies_count: `${obj[0]}`,
                    group_policies_count: `${obj[1]}`,
                    expression_policies_count: `${obj[2]}`,
                },
            },
        ]),
    ),
};

export function setup() {
    let cookies = {};
    for (let vu = 0; vu < VUs; vu++) {
        cookies[vu] = {};
        for (const testcase of testcases) {
            const user_policies_count = testcase[0];
            const group_policies_count = testcase[1];
            const expression_policies_count = testcase[2];
            const domain = `provider-oauth2-${user_policies_count}-${group_policies_count}-${expression_policies_count}.${host}:9000`;
            const url = http.url`http://${domain}/api/v3/flows/executor/default-authentication-flow/`;
            const params = {
                headers: {
                    "Content-Type": "application/json",
                    Accept: "*/*",
                },
            };
            http.cookieJar().clear(`http://${domain}`);
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
                } else if (component === "xak-flow-redirect") {
                    break;
                } else {
                    fail(`Unknown component type: ${component}`);
                    break;
                }

                payload["component"] = component;
                res = http.post(url, JSON.stringify(payload), params);
                i++;
            }
            cookies[vu][domain] = http
                .cookieJar()
                .cookiesForURL(`http://${domain}`);
        }
    }
    return { cookies };
}

export default function (data) {
    // Restore cookies
    let jar = http.cookieJar();
    const vu = exec.vu.idInTest % VUs;
    Object.keys(data.cookies[vu]).forEach((domain) => {
        Object.keys(data.cookies[vu][domain]).forEach((key) => {
            jar.set(`http://${domain}`, key, data.cookies[vu][domain][key][0]);
        });
    });

    const user_policies_count = Number(__ENV.USER_POLICIES_COUNT);
    const group_policies_count = Number(__ENV.GROUP_POLICIES_COUNT);
    const expression_policies_count = Number(__ENV.EXPRESSION_POLICIES_COUNT);
    const domain = `provider-oauth2-${user_policies_count}-${group_policies_count}-${expression_policies_count}.${host}:9000`;
    const params = {
        headers: {
            "Content-Type": "application/json",
            Accept: "*/*",
        },
    };

    const random = (length = 32) => {
        let chars =
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
        let str = "";
        for (let i = 0; i < length; i++) {
            str += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return str;
    };

    const state = random(32);
    const nonce = random(32);
    const code_verifier = random(64);
    const code_challenge = crypto.sha256(code_verifier, "base64");
    const urlParams = {
        response_type: "code",
        scope: "openid profile email",
        client_id: "123456",
        redirect_uri: "http://test.localhost",
        state: state,
        nonce: nonce,
        code_challenge: code_challenge,
        code_challenge_method: "S256",
    };

    let url = http.url`http://${domain}/application/o/authorize/?${Object.entries(
        urlParams,
    )
        .map((kv) => kv.map(encodeURIComponent).join("="))
        .join("&")}`;
    let res = http.get(url, params);
    check(res, {
        "status is 200": (res) => res.status === 200,
    });
    if (res.status !== 200) {
        fail("Endpoint did not return 200.");
        return;
    }

    url = http.url`http://${domain}/api/v3/flows/executor/default-provider-authorization-implicit-consent/`;
    res = http.get(url, params);
    check(res, {
        "status is 200": (res) => res.status === 200,
        "last redirect is present": (res) => res.json()["type"] === "redirect",
    });
    if (res.status !== 200) {
        fail("Endpoint did not return 200.");
        return;
    }
}
