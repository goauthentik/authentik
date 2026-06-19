import { LitViteContext } from "./rendering.js";

import { page } from "@vitest/browser/context";
import { beforeEach } from "vitest";

page.extend({
    // @ts-expect-error Extension is not properly typed.
    renderLit: LitViteContext.render,
    [Symbol.for("vitest:component-cleanup")]: LitViteContext.cleanup,
});

beforeEach(() => LitViteContext.cleanup());
