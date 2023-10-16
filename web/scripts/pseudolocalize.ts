import { readFileSync } from "fs";
import path from "path";
import pseudolocale from "pseudolocale";
import { fileURLToPath } from "url";

import { makeFormatter } from "@lit/localize-tools/lib/formatters/index.js";
import type { Message, ProgramMessage } from "@lit/localize-tools/lib/messages.d.ts";
import { sortProgramMessages } from "@lit/localize-tools/lib/messages.js";
import { TransformLitLocalizer } from "@lit/localize-tools/lib/modes/transform.js";
import type { Config } from "@lit/localize-tools/lib/types/config.d.ts";
import type { Locale } from "@lit/localize-tools/lib/types/locale.d.ts";
import type { TransformOutputConfig } from "@lit/localize-tools/lib/types/modes.d.ts";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const pseudoLocale: Locale = "pseudo-LOCALE" as Locale;
const targetLocales: Locale[] = [pseudoLocale];
const baseConfig = JSON.parse(readFileSync(path.join(__dirname, "../lit-localize.json"), "utf-8"));

// Need to make some internal specifications to satisfy the transformer. It doesn't actually matter
// which Localizer we use (transformer or runtime), because all of the functionality we care about
// is in their common parent class, but I had to pick one.  Everything else here is just pure
// exploitation of the lit/localize-tools internals.

const config: Config = {
    ...baseConfig,
    baseDir: path.join(__dirname, ".."),
    targetLocales,
    output: {
        ...baseConfig,
        mode: "transform",
    },
    resolve: (path: string) => path,
} as Config;

const pseudoMessagify = (message: ProgramMessage) => ({
    name: message.name,
    contents: message.contents.map((content) =>
        typeof content === "string" ? pseudolocale(content, { prepend: "", append: "" }) : content,
    ),
});

const localizer = new TransformLitLocalizer(config as Config & { output: TransformOutputConfig });
const { messages } = localizer.extractSourceMessages();
const translations = messages.map(pseudoMessagify);
const sorted = sortProgramMessages([...messages]);
const formatter = makeFormatter(config);
formatter.writeOutput(sorted, new Map<Locale, Message[]>([[pseudoLocale, translations]]));
