import exec from "k6/execution";
import http from "k6/http";
import { check } from "k6";

const host = __ENV.BENCH_HOST ? __ENV.BENCH_HOST : "localhost";
const VUs = __ENV.VUS ? __ENV.VUS : 8;

export const options = {
    discardResponseBodies: true,
    scenarios: Object.fromEntries(
        [
            // Number of groups, number of users per group, with parent, page size, include users
            [1000, 0, false, 20, false],
            [10000, 0, false, 20, false],
            [1000, 0, false, 100, false],
            [10000, 0, false, 100, false],
            [1000, 1000, false, 100, false],
            [1000, 10000, false, 100, false],
            [1000, 1000, false, 100, true],
            [1000, 10000, false, 100, true],
            [1000, 0, true, 100, false],
            [10000, 0, true, 100, false],
        ].map((obj, i) => [
            `${obj[0]}_${obj[1]}_${obj[2] ? "with_parents" : "without_parents"}_${obj[3]}_${obj[4] ? "with_users" : "without_users"}`,
            {
                executor: "constant-vus",
                vus: VUs,
                duration: "150s",
                startTime: `${165 * i}s`,
                env: {
                    GROUP_COUNT: `${obj[0]}`,
                    USERS_PER_GROUP: `${obj[1]}`,
                    WITH_PARENTS: `${obj[2]}`,
                    PAGE_SIZE: `${obj[3]}`,
                    WITH_USERS: `${obj[4] ? "true" : "false"}`,
                },
                tags: {
                    testid: `group_list_${obj[0]}_${obj[1]}_${obj[2] ? "with_parents" : "without_parents"}_${obj[3]}_${obj[4] ? "with_users" : "without_users"}`,
                    group_count: `${obj[0]}`,
                    users_per_group: `${obj[1]}`,
                    with_parents: `${obj[2]}`,
                    page_size: `${obj[3]}`,
                    with_users: `${obj[4] ? "true" : "false"}`,
                },
            },
        ]),
    ),
};

export default function () {
    const group_count = Number(__ENV.GROUP_COUNT);
    const users_per_group = Number(__ENV.USERS_PER_GROUP);
    const with_parents = __ENV.WITH_PARENTS;
    const with_users = __ENV.WITH_USERS;
    const domain = `group-list-${group_count}-${users_per_group}-${with_parents}.${host}:9000`;
    const page_size = Number(__ENV.PAGE_SIZE);
    const pages = Math.round(group_count / page_size);
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
                http.url`http://${domain}/api/v3/core/groups/?page=${page}&page_size=${page_size}&include_users=${with_users}`,
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
                http.url`http://${domain}/api/v3/core/groups/?page=${page}&page_size=${page_size}&include_users=${with_users}`,
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
