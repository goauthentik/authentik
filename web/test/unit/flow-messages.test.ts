import { MessageLevel } from "#common/messages";

import { flowMessageLevel, flowMessages } from "#flow/messages";

import { FlowMessage, FlowMessageLevelEnum } from "@goauthentik/api";

import { describe, expect, it } from "vitest";

const makeFlowMessage = (level: FlowMessageLevelEnum, message: string): FlowMessage => ({
    level,
    message,
});

describe("flowMessageLevel", () => {
    it("maps each level the server can send to its interface counterpart", () => {
        expect(flowMessageLevel(FlowMessageLevelEnum.Error)).toBe(MessageLevel.error);
        expect(flowMessageLevel(FlowMessageLevelEnum.Warning)).toBe(MessageLevel.warning);
        expect(flowMessageLevel(FlowMessageLevelEnum.Success)).toBe(MessageLevel.success);
        expect(flowMessageLevel(FlowMessageLevelEnum.Info)).toBe(MessageLevel.info);
    });

    it("displays debug as info, as the interface has no debug level", () => {
        expect(flowMessageLevel(FlowMessageLevelEnum.Debug)).toBe(MessageLevel.info);
    });

    it("displays a level added by a newer server as info", () => {
        expect(flowMessageLevel(FlowMessageLevelEnum.UnknownDefaultOpenApi)).toBe(
            MessageLevel.info,
        );
    });
});

describe("flowMessages", () => {
    it("converts every message attached to a challenge", () => {
        const messages = [
            makeFlowMessage(FlowMessageLevelEnum.Success, "Email successfully sent."),
            makeFlowMessage(FlowMessageLevelEnum.Error, "Failed to authenticate."),
        ];

        expect(flowMessages(messages)).toEqual([
            { level: MessageLevel.success, message: "Email successfully sent." },
            { level: MessageLevel.error, message: "Failed to authenticate." },
        ]);
    });

    it("returns nothing for a challenge without messages", () => {
        expect(flowMessages(undefined)).toEqual([]);
        expect(flowMessages(null)).toEqual([]);
        expect(flowMessages([])).toEqual([]);
    });
});
