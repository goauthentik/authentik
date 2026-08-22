import { compile, run } from "@mdx-js/mdx";
import { renderToStaticMarkup } from "react-dom/server";
import * as runtime from "react/jsx-runtime";
import { describe, expect, it } from "vitest";

/**
 * `<ak-mdx>` renders sources of two different kinds:
 *
 * - documentation bundled with the web interface, referenced by `url`, which is
 *   authored in-tree and compiled as MDX,
 * - content returned by the API, passed as `content` — user and group notes,
 *   and blueprint descriptions — which is compiled as CommonMark.
 *
 * The distinction matters because MDX evaluates expressions and ESM
 * imports/exports of a source when the compiled module runs, while CommonMark
 * has no evaluated syntax at all. These tests cover that the format the
 * element passes to the compiler decides whether a source is evaluated.
 */
async function renderWithFormat(source: string, format: "md" | "mdx"): Promise<string> {
    const compiled = await compile(source, { format, outputFormat: "function-body" });
    const { default: Content } = await run(compiled, { ...runtime, baseUrl: import.meta.url });

    return renderToStaticMarkup(Content({}));
}

/**
 * A source can only report back that it was evaluated by reaching outside of
 * itself, so the compiled sources below call into this global.
 */
const probeGlobal = globalThis as typeof globalThis & {
    __akMDXFormatProbe?: string[];
};

function withProbe<T>(body: (calls: string[]) => Promise<T>): Promise<T> {
    const calls: string[] = [];

    probeGlobal.__akMDXFormatProbe = calls;

    return body(calls).finally(() => {
        delete probeGlobal.__akMDXFormatProbe;
    });
}

const EXPRESSION_SOURCE = `Release notes {globalThis.__akMDXFormatProbe?.push("expression")}`;
const ESM_SOURCE = `export const note = globalThis.__akMDXFormatProbe?.push("esm");\n\nRelease notes`;

describe("ak-mdx content format", () => {
    it("evaluates expressions and ESM when compiled as MDX", async () => {
        await withProbe(async (calls) => {
            await renderWithFormat(EXPRESSION_SOURCE, "mdx");
            await renderWithFormat(ESM_SOURCE, "mdx");

            expect(calls).toEqual(["expression", "esm"]);
        });
    });

    it("does not evaluate expressions when compiled as CommonMark", async () => {
        await withProbe(async (calls) => {
            const markup = await renderWithFormat(EXPRESSION_SOURCE, "md");

            expect(calls).toEqual([]);
            expect(markup).toContain("__akMDXFormatProbe");
        });
    });

    it("does not evaluate ESM when compiled as CommonMark", async () => {
        await withProbe(async (calls) => {
            const markup = await renderWithFormat(ESM_SOURCE, "md");

            expect(calls).toEqual([]);
            expect(markup).toContain("export const note");
        });
    });

    it("still renders CommonMark features", async () => {
        const markup = await renderWithFormat(
            "## Heading\n\n**bold** and _italic_\n\n- one\n- two\n",
            "md",
        );

        expect(markup).toContain("<h2>Heading</h2>");
        expect(markup).toContain("<strong>bold</strong>");
        expect(markup).toContain("<em>italic</em>");
        expect(markup).toContain("<li>one</li>");
    });
});
