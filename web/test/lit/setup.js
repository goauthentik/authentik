import { LitViteContext } from "./rendering.js";

import { page } from "@vitest/browser/context";
import { beforeEach } from "vitest";

page.extend({
    // @ts-ignore
    renderLit: LitViteContext.render,
    [Symbol.for("vitest:component-cleanup")]: LitViteContext.cleanup,
});

beforeEach(() => LitViteContext.cleanup());
