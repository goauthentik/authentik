import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import pseudolocale from "pseudolocale";

import { makeFormatter } from "@lit/localize-tools/lib/formatters/index.js";
import { sortProgramMessages } from "@lit/localize-tools/lib/messages.js";
import { TransformLitLocalizer } from "@lit/localize-tools/lib/modes/transform.js";

const relativeDirname = fileURLToPath(new URL(".", import.meta.url));
const pseudoLocale = "pseudo-LOCALE";
const targetLocales = [pseudoLocale];
const baseConfig = JSON.parse(
    readFileSync(path.join(relativeDirname, "../lit-localize.json"), "utf-8"),
);

// Need to make some internal specifications to satisfy the transformer. It doesn't actually matter
// which Localizer we use (transformer or runtime), because all of the functionality we care about
// is in their common parent class, but I had to pick one.  Everything else here is just pure
// exploitation of the lit/localize-tools internals.

const config = {
    ...baseConfig,
    baseDir: path.join(relativeDirname, ".."),
    targetLocales,
    output: {
        ...baseConfig.output,
        mode: "transform",
    },
    resolve: (path) => path,
};

const pseudoMessagify = (message) => ({
    name: message.name,
    contents: message.contents.map((content) =>
        typeof content === "string" ? pseudolocale(content, { prepend: "", append: "" }) : content,
    ),
});

const localizer = new TransformLitLocalizer(config);
const messages = localizer.extractSourceMessages().messages;
const translations = messages.map(pseudoMessagify);
const sorted = sortProgramMessages([...messages]);
const formatter = makeFormatter(config);

formatter.writeOutput(
    sorted,
    // @ts-expect-error Needs typing.
    new Map([[pseudoLocale, translations]]),
);
