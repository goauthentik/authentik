import exec from "k6/execution";
import { command } from "k6/x/exec";
import http from "k6/http";
import { check, group } from "k6";

export const options = {
    discardResponseBodies: true,
    scenarios: Object.fromEntries(
        [
            [10, 20],
            [100, 20],
            [1000, 20],
            [10000, 20],
            [10, 100],
            [100, 100],
            [1000, 100],
            [10000, 100],
        ].map((obj, i) => [
            `${obj[0]}_${obj[1]}`,
            {
                executor: "constant-vus",
                vus: 10,
                duration: "10s",
                startTime: `${10 * i}s`,
                env: {
                    USER_COUNT: `${obj[0]}`,
                    PAGE_SIZE: `${obj[1]}`,
                },
                tags: {
                    user_count: `${obj[0]}`,
                    page_size: `${obj[1]}`,
                },
            },
        ]),
    ),
};

export function setup() {
    command("./create_users.py", ["11000"]);
}

export function teardown() {
    command("./delete_users.py");
}

export default function () {
    const user_count = Number(__ENV.USER_COUNT);
    const page_size = Number(__ENV.PAGE_SIZE);
    const pages = Math.round(user_count / 20);
    let requests = [];
    for (let page = 1; page <= pages; page++) {
        requests.push([
            "GET",
            `http://localhost:9000/api/v3/core/users/?page=${page}&page_size=${page_size}`,
            null,
            {
                headers: {
                    Authorization: "Bearer akadmin",
                    "Content-Type": "application/json",
                    Accept: "*/*",
                },
                tags: {
                    name: "/core/users/",
                },
            },
        ]);
    }
    const responses = http.batch(requests);
    for (let page = 1; page <= pages; page++) {
        check(responses[page - 1], {
            "status is 200": (res) => res.status === 200,
        });
    }
}
