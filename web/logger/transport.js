/**
 * @import {PrettyOptions} from "pino-pretty"
 * @file Pretty transport for Pino
 */

import PinoPretty from "pino-pretty";

/**
 * @param {PrettyOptions} options
 */
function prettyTransporter(options) {
    const pretty = PinoPretty({
        ...options,
        ignore: "pid,hostname",
        translateTime: "SYS:HH:MM:ss",
    });

    return pretty;
}

export default prettyTransporter;
