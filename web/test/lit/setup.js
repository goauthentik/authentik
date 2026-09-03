import { LitViteContext } from "./rendering.js";

import { beforeEach } from "vitest";
import { page } from "vitest/browser";

page.extend({
    // @ts-expect-error Extension is not properly typed.
    renderLit: LitViteContext.render,
    [Symbol.for("vitest:component-cleanup")]: LitViteContext.cleanup,
});

beforeEach(() => LitViteContext.cleanup());
