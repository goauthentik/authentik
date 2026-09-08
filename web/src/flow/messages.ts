/**
 * @file Messages sent to the client as part of a flow challenge.
 */

import { APIMessage, MessageLevel } from "#common/messages";

import { FlowMessage, FlowMessageLevelEnum } from "@goauthentik/api";

/**
 * Map the level of a message sent as flow data to the level used by the interface.
 *
 * @remarks
 * `debug` has no counterpart in the interface, and is displayed as info. The server only ever
 * sends it when the message level is lowered from its default.
 */
export function flowMessageLevel(level: FlowMessageLevelEnum): MessageLevel {
    switch (level) {
        case FlowMessageLevelEnum.Error:
            return MessageLevel.error;
        case FlowMessageLevelEnum.Warning:
            return MessageLevel.warning;
        case FlowMessageLevelEnum.Success:
            return MessageLevel.success;
        default:
            return MessageLevel.info;
    }
}

/**
 * Convert the messages attached to a challenge into messages ready to be displayed.
 *
 * @remarks
 * The server attaches a message to a single challenge and considers it delivered from then on, so
 * callers must display these as soon as a challenge is received. Redirect challenges never carry
 * messages, since the client navigates away before they could be read; those are delivered by the
 * page navigated to instead.
 */
export function flowMessages(messages: FlowMessage[] | null | undefined): APIMessage[] {
    if (!messages) return [];

    return messages.map(({ level, message }) => ({
        level: flowMessageLevel(level),
        message,
    }));
}
