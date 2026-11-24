import { appHasLaunchUrl } from "#user/LibraryPage/LibraryPageImpl.utils";

import type { Application } from "@goauthentik/api";

import { expect, it } from "vitest";

it("keeps an application visible when its relative launch URL has a URL in its query", () => {
    const app = { launchUrl: "/docs/?example=ssh://host" } as Application;

    expect(appHasLaunchUrl(app)).toBe(true);
});
