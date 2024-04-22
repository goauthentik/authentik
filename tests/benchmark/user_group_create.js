import exec from "k6/execution";
import http from "k6/http";
import { check } from "k6";

const host = __ENV.BENCH_HOST ? __ENV.BENCH_HOST : "localhost";
const VUs = __ENV.VUS ? __ENV.VUS : 8;

export const options = {
    vus: VUs,
    duration: "150s",
    tags: {
        testid: `user-group-create`,
    },
};

export default function () {
    const domain = `user-group-create.${host}:9000`;
    const params = {
        headers: {
            Authorization: "Bearer akadmin",
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

    let user_res = http.post(
        http.url`http://${domain}/api/v3/core/users/`,
        JSON.stringify({
            username: random(16),
            name: random(16),
        }),
        params,
    );
    check(user_res, {
        "user status is 201": (res) => res.status === 201,
    });

    let group_res = http.post(
        http.url`http://${domain}/api/v3/core/groups/`,
        JSON.stringify({
            name: random(16),
        }),
        params,
    );
    check(group_res, {
        "group status is 201": (res) => res.status === 201,
    });

    let user_group_res = http.post(
        http.url`http://${domain}/api/v3/core/groups/${group_res.json()["pk"]}/add_user/`,
        JSON.stringify({
            pk: user_res.json()["pk"],
        }),
        params,
    );
    check(user_group_res, {
        "user group status is 204": (res) => res.status === 204,
    });
}
