import exec from "k6/execution";
import http from "k6/http";
import { check } from "k6";

const host = __ENV.BENCH_HOST ? __ENV.BENCH_HOST : "localhost";
const VUs = __ENV.VUS ? __ENV.VUS : 8;

export const options = {
    discardResponseBodies: true,
    scenarios: Object.fromEntries(
        [
            // Number of events, page size
            [1000, 100],
            [10000, 20],
            [10000, 100],
            [100000, 100],
            [1000000, 100],
        ].map((obj, i) => [
            `${obj[0]}_${obj[1]}`,
            {
                executor: "constant-vus",
                vus: VUs,
                duration: "150s",
                startTime: `${165 * i}s`,
                env: {
                    EVENT_COUNT: `${obj[0]}`,
                    PAGE_SIZE: `${obj[1]}`,
                },
                tags: {
                    testid: `event_list_${obj[0]}_${obj[1]}`,
                    event_count: `${obj[0]}`,
                    page_size: `${obj[1]}`,
                },
            },
        ]),
    ),
};

export default function () {
    const event_count = Number(__ENV.EVENT_COUNT);
    const domain = `event-list-${event_count}.${host}:9000`;
    const page_size = Number(__ENV.PAGE_SIZE);
    const pages = Math.round(event_count / page_size);
    const params = {
        headers: {
            Authorization: "Bearer akadmin",
            "Content-Type": "application/json",
            Accept: "*/*",
        },
    };

    if (pages <= 10) {
        for (let page = 1; page <= pages; page++) {
            let res = http.get(
                http.url`http://${domain}/api/v3/events/events/?page=${page}&page_size=${page_size}`,
                params,
            );
            check(res, {
                "status is 200": (res) => res.status === 200,
            });
        }
    } else {
        let requests = [];
        for (let page = 1; page <= pages; page++) {
            requests.push([
                "GET",
                http.url`http://${domain}/api/v3/events/events/?page=${page}&page_size=${page_size}`,
                null,
                params,
            ]);
        }
        const responses = http.batch(requests);
        for (let page = 1; page <= pages; page++) {
            check(responses[page - 1], {
                "status is 200": (res) => res.status === 200,
            });
        }
    }
}
