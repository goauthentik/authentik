/**
 * @file Pretty transport for Pino
 */

import PinoPretty, { type PrettyOptions } from "pino-pretty";

function prettyTransporter(options: PrettyOptions) {
    const pretty = PinoPretty({
        ...options,
        ignore: "pid,hostname",
        translateTime: "SYS:HH:MM:ss",
    });

    return pretty;
}

export default prettyTransporter;
