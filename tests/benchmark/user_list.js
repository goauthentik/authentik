import exec from "k6/execution";
import http from "k6/http";
import { check } from "k6";

export const options = {
    discardResponseBodies: true,
    scenarios: Object.fromEntries(
        [
            // Number of users, number of groups per user, number of parents per group, page size, with groups
            [10, 0, 0, 20, true],
            [100, 0, 0, 20, true],
            [1000, 0, 0, 20, true],
            [10000, 0, 0, 20, true],
            [1000, 0, 0, 20, false],
            [10000, 0, 0, 20, false],
            [10, 0, 0, 100, true],
            [100, 0, 0, 100, true],
            [1000, 0, 0, 100, true],
            [10000, 0, 0, 100, true],
            [100, 3, 0, 20, true],
            [1000, 3, 0, 20, true],
            [10000, 3, 0, 20, true],
            [100, 20, 0, 20, true],
            [1000, 20, 0, 20, true],
            [10000, 20, 0, 20, true],
            [100, 20, 3, 20, true],
            [1000, 20, 3, 20, true],
            [10000, 20, 3, 20, true],
            [100, 20, 0, 20, false],
            [1000, 20, 0, 20, false],
            [10000, 20, 0, 20, false],
            [100, 20, 3, 20, false],
            [1000, 20, 3, 20, false],
            [10000, 20, 3, 20, false],
        ].map((obj, i) => [
            `${obj[0]}_${obj[1]}_${obj[2]}_${obj[3]}_${obj[4] ? "with_groups" : "without_groups"}`,
            {
                executor: "constant-vus",
                vus: 12,
                duration: "300s",
                startTime: `${315 * i}s`,
                env: {
                    USER_COUNT: `${obj[0]}`,
                    GROUPS_PER_USER: `${obj[1]}`,
                    PARENTS_PER_GROUP: `${obj[2]}`,
                    PAGE_SIZE: `${obj[3]}`,
                    WITH_GROUPS: `${obj[4]}`,
                },
                tags: {
                    testid: `user_list_${obj[0]}_${obj[1]}_${obj[2]}_${obj[3]}_${obj[4] ? "with_groups" : "without_groups"}`,
                    user_count: `${obj[0]}`,
                    groups_per_user: `${obj[1]}`,
                    parents_per_group: `${obj[2]}`,
                    page_size: `${obj[3]}`,
                    with_groups: `${obj[4]}`,
                },
            },
        ]),
    ),
};

export default function () {
    const user_count = Number(__ENV.USER_COUNT);
    const groups_per_user = Number(__ENV.GROUPS_PER_USER);
    const parents_per_group = Number(__ENV.PARENTS_PER_GROUP);
    const with_groups = Number(__ENV.WITH_GROUPS);
    const domain = `user-list-${user_count}-${groups_per_user}-${parents_per_group}`;
    const page_size = Number(__ENV.PAGE_SIZE);
    const pages = Math.round(user_count / page_size);
    let requests = [];
    for (let page = 1; page <= pages; page++) {
        requests.push([
            "GET",
            `http://${domain}.localhost:9000/api/v3/core/users/?page=${page}&page_size=${page_size}&include_groups=${with_groups}`,
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
