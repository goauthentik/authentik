import { createReadStream } from "node:fs";

import {
    PLACEHOLDER,
    ParseError,
    type TranslationEntry,
    type TranslationReader,
} from "#translation/shared";

import { SaxParser } from "@nodable/sax";

//#region Inline content

/**
 * Inline elements that stand in for markup or code. Their content is never translated text.
 */
const PLACEHOLDER_ELEMENTS = new Set(["x", "bx", "ex", "ph", "it", "sc", "ec", "bpt", "ept"]);

/**
 * Inline elements that wrap translated text.
 */
const CONTAINER_ELEMENTS = new Set(["g", "mrk", "pc"]);

//#endregion

//#region Reader

interface PendingSegment {
    id: string;
    source: string;
    target: string | null;
}

interface PendingUnit {
    key: string;
    line: number;
    translate: boolean;
    segments: PendingSegment[];
}

/**
 * Stream translation entries from an XLIFF 1.2 or 2.x file.
 *
 * Units are yielded as their elements close; the next chunk is read only once those are consumed.
 */
export const readXLIFF = async function* (filePath) {
    const ready: TranslationEntry[] = [];

    let version: "1.2" | "2" | null = null;
    let locale = "";
    let unit: PendingUnit | null = null;
    let segment: PendingSegment | null = null;
    /**
     * Which text is being collected, and the inline element depth inside it.
     */
    let capture: { field: "source" | "target"; text: string; depth: number } | null = null;
    /**
     * Depth inside a placeholder element whose content is skipped.
     */
    let skipDepth = 0;

    /**
     * Character offsets of every newline read so far, for mapping parser offsets to lines.
     */
    const newlines: number[] = [];
    let consumed = 0;

    const lineAt = (offset: number): number => {
        let low = 0;
        let high = newlines.length;

        while (low < high) {
            const mid = (low + high) >>> 1;

            if (newlines[mid]! < offset) {
                low = mid + 1;
            } else {
                high = mid;
            }
        }

        return low + 1;
    };

    const fail = (reason: string): never => {
        throw new ParseError(`${filePath}: ${reason}`);
    };

    const parser = new SaxParser({
        fxpOptions: {
            skip: { attributes: false, nsPrefix: true, whitespaceText: false },
        },
        onStartElement(
            name: string,
            attributes: Record<string, string>,
            tagDetail: { index: number },
        ) {
            if (skipDepth) {
                skipDepth++;
                return;
            }

            if (capture) {
                capture.depth++;

                if (name === "cp") {
                    capture.text += String.fromCodePoint(Number.parseInt(attributes.hex ?? "", 16));
                } else if (PLACEHOLDER_ELEMENTS.has(name)) {
                    capture.text += PLACEHOLDER;
                    skipDepth = 1;
                } else if (!CONTAINER_ELEMENTS.has(name)) {
                    fail(`unsupported inline element <${name}>`);
                }

                return;
            }

            switch (name) {
                case "xliff": {
                    const declared = attributes.version ?? "";

                    if (declared === "1.2") {
                        version = "1.2";
                    } else if (declared === "2.0" || declared === "2.1") {
                        version = "2";
                    } else {
                        fail(`unsupported XLIFF version "${declared}"`);
                    }

                    locale = attributes.trgLang ?? "";
                    return;
                }
                case "file": {
                    const language = attributes["target-language"];

                    if (language && locale && language !== locale) {
                        fail("conflicting target languages");
                    }

                    locale ||= language ?? "";
                    return;
                }
                case "trans-unit":
                case "unit": {
                    if (!attributes.id) {
                        fail(`<${name}> without an id`);
                    }

                    unit = {
                        key: attributes.id!,
                        line: lineAt(tagDetail.index),
                        translate: attributes.translate !== "no",
                        segments: [],
                    };

                    // XLIFF 1.2 has no segment element: the unit is the segment.
                    if (version === "1.2") {
                        segment = { id: "", source: "", target: null };
                    }

                    return;
                }
                case "segment": {
                    if (unit) {
                        segment = {
                            id: attributes.id ?? String(unit.segments.length),
                            source: "",
                            target: null,
                        };
                    }

                    return;
                }
                case "source":
                case "target": {
                    if (segment) {
                        capture = { field: name, text: "", depth: 0 };
                    }

                    return;
                }
            }
        },
        onText(text: string) {
            if (capture && !skipDepth) {
                capture.text += text;
            }
        },
        onCData(text: string) {
            if (capture && !skipDepth) {
                capture.text += text;
            }
        },
        onEndElement(name: string) {
            if (skipDepth) {
                skipDepth--;

                if (capture && !skipDepth) {
                    capture.depth--;
                }
                return;
            }

            if (capture?.depth) {
                capture.depth--;
                return;
            }

            if (capture && segment && (name === "source" || name === "target")) {
                if (name === "source") {
                    segment.source = capture.text;
                } else {
                    segment.target = capture.text;
                }

                capture = null;
                return;
            }

            if (name === "segment" && unit && segment) {
                unit.segments.push(segment);
                segment = null;
                return;
            }

            if ((name === "trans-unit" || name === "unit") && unit) {
                if (version === "1.2" && segment) {
                    unit.segments.push(segment);
                }

                const multiple = unit.segments.length > 1;

                for (const { id, source, target } of unit.translate ? unit.segments : []) {
                    ready.push({
                        format: "xlf",
                        locale,
                        id: unit.key,
                        segment: multiple ? id : undefined,
                        line: unit.line,
                        source,
                        target: target ?? "",
                    });
                }

                unit = null;
                segment = null;
            }
        },
    });

    using stack = new DisposableStack();
    const stream = stack.adopt(createReadStream(filePath, { encoding: "utf8" }), (s) =>
        s.destroy(),
    );

    for await (const chunk of stream) {
        const text = chunk as string;

        for (let i = text.indexOf("\n"); i !== -1; i = text.indexOf("\n", i + 1)) {
            newlines.push(consumed + i);
        }

        consumed += text.length;
        parser.write(text);
        yield* ready.splice(0);
    }

    parser.end();
    yield* ready.splice(0);

    if (!version) {
        fail("no <xliff> root element");
    }
} satisfies TranslationReader;

//#endregion
