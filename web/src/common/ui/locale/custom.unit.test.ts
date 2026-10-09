import { createCustomTemplates, parseTranslation } from "#common/ui/locale/custom";

import { describe, expect, it, vi } from "vitest";

import { str } from "@lit/localize";
import { generateMsgId } from "@lit/localize/internal/id-generation.js";
import { runtimeMsg } from "@lit/localize/internal/runtime-msg.js";

vi.mock("#common/api/client", () => ({ aki: vi.fn() }));

describe("parseTranslation", () => {
    it("keeps translations without placeholders as strings", () => {
        expect(parseTranslation("Benutzerkennung")).toBe("Benutzerkennung");
    });

    it("converts placeholders to a str template", () => {
        const name = "authentik";
        const count = 3;
        const template = parseTranslation("${1} Dinge in ${0}");

        expect(runtimeMsg({ id: template }, str`${name} has ${count} things`, { id: "id" })).toBe(
            "3 Dinge in authentik",
        );
    });
});

describe("createCustomTemplates", () => {
    it("keys templates by message ID and by source string", () => {
        const templates = createCustomTemplates({
            "Username": "Kennung",
            "captcha.label": "Robotertest",
        });

        expect(templates.Username).toBe("Kennung");
        expect(templates[generateMsgId("Username", false)]).toBe("Kennung");
        expect(templates["captcha.label"]).toBe("Robotertest");
    });

    it("matches source strings with expressions", () => {
        const name = "authentik";
        const templates = createCustomTemplates({ "Welcome to ${0}": "Willkommen bei ${0}" });

        expect(runtimeMsg(templates, str`Welcome to ${name}`, undefined)).toBe(
            "Willkommen bei authentik",
        );
    });
});
