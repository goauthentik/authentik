/**
 * @file Pretty transport for Pino
 */

import PinoPretty, { type PrettyOptions } from "pino-pretty";

function prettyTransporter(options: PrettyOptions) {
    return PinoPretty({
        ...options,
        ignore: "pid,hostname",
        translateTime: "SYS:HH:MM:ss",
    });
}

export default prettyTransporter;
