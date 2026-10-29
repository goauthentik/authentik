import { aki } from "#common/api/client";

import { DebugApi } from "@goauthentik/api";

let _serverLog = async (_: string): Promise<void> => {};

if (process.env.NODE_ENV !== "production") {
    _serverLog = async (msg): Promise<void> => {
        const api = await aki(DebugApi);

        api.debugLogCreate({
            serverLogRequest: {
                message: msg,
            },
        });
    };
}

export function serverLog(msg: string) {
    return _serverLog(msg);
}
