/**
 * @remarks
 *   Uses `monaco-yaml`, which runs Red Hat's YAML language server in a web worker.
 * @file YAML suggestions, hovers and validation from the editor's schema.
 */

import { SchemaRegistry } from "#elements/CodeEditor/languages/schemas";
import type { LanguageService } from "#elements/CodeEditor/languages/types";
import YAMLWorkerURL from "#elements/CodeEditor/languages/yaml.worker?worker&url";

import * as monaco from "monaco-editor/editor/editor.api";
import { configureMonacoYaml } from "monaco-yaml";

/**
 * The tags blueprints may use, by the YAML node each one takes.
 *
 * @see {@link https://docs.goauthentik.io/customize/blueprints/v1/tags}
 */
const ScalarTags = ["KeyOf", "ParseJSON", "Index", "Value"];
const ScalarOrSequenceTags = ["Env", "File", "Context"];
const SequenceTags = ["Format", "Find", "FindObject", "Condition", "If", "Enumerate", "AtIndex"];

const BlueprintTags = [
    ...ScalarTags.map((tag) => `!${tag} scalar`),
    ...ScalarOrSequenceTags.flatMap((tag) => [`!${tag} scalar`, `!${tag} sequence`]),
    ...SequenceTags.map((tag) => `!${tag} sequence`),
];

/**
 * Matches the text before a value that a blueprint tag applies to.
 */
const TagBeforeValuePattern = new RegExp(
    `!(${[...ScalarTags, ...ScalarOrSequenceTags, ...SequenceTags].join("|")})\\s+$`,
);

/**
 * Whether the marked value follows a blueprint tag, on its line or at the end of an earlier one.
 */
function isTagged(model: monaco.editor.ITextModel, marker: monaco.editor.IMarker): boolean {
    let line = marker.startLineNumber;
    let before = model.getLineContent(line).slice(0, marker.startColumn - 1);

    while (!before.trim() && line > 1) {
        line -= 1;
        before = `${model.getLineContent(line)} `;
    }

    return TagBeforeValuePattern.test(before);
}

/**
 * Drops the schema errors on tagged values.
 *
 * @remarks
 *   A tag resolves when the blueprint is applied, e.g. `!Format [...]` to a string, but the
 *   language server checks the YAML as written, so it reports the sequence as the wrong type.
 */
monaco.editor.onDidChangeMarkers((resources) => {
    for (const resource of resources) {
        const model = monaco.editor.getModel(resource);

        if (model?.getLanguageId() !== "yaml") continue;

        const markers = monaco.editor.getModelMarkers({ owner: "yaml", resource });

        const kept = markers.filter((marker) => !isTagged(model, marker));

        // Setting markers fires this listener again, with nothing left to drop.
        if (kept.length !== markers.length) {
            monaco.editor.setModelMarkers(model, "yaml", kept);
        }
    }
});

interface LegacyWebWorkerOptions {
    label?: string;
    createData?: unknown;
}

/**
 * Starts the bundled worker for `monaco-yaml`, which still passes the options Monaco took before
 * it left creating the worker to the caller.
 */
function createWebWorker(
    options: monaco.editor.IInternalWebWorkerOptions | LegacyWebWorkerOptions,
) {
    if ("worker" in options) {
        return monaco.editor.createWebWorker(options);
    }

    const worker = new Worker(new URL(YAMLWorkerURL, import.meta.url), {
        type: "module",
        name: options.label,
    });

    // The same handshake Monaco's own language workers expect.
    worker.postMessage("ignore");
    worker.postMessage(options.createData);

    return monaco.editor.createWebWorker({ worker });
}

const registry = new SchemaRegistry();

/**
 * Options the language server takes that `monaco-yaml` passes on without declaring.
 */
interface LanguageServerOptions {
    /**
     * Whether hovers end with a link to their schema, which here is a hashed file name.
     */
    hoverSchemaSource?: boolean;
}

const monacoYAML = configureMonacoYaml(
    { ...monaco, editor: { ...monaco.editor, createWebWorker } } as unknown as Parameters<
        typeof configureMonacoYaml
    >[0],
    {
        enableSchemaRequest: true,
        customTags: BlueprintTags,
        // The editor does not offer formatting.
        format: { enable: false },
        hoverSchemaSource: false,
        schemas: [],
    } as Parameters<typeof configureMonacoYaml>[1] & LanguageServerOptions,
);

// Each change restarts the worker, which then fetches its schemas again from the browser cache.
registry.onDidChange(() => {
    monacoYAML.update({ schemas: registry.toAssociations() });
});

export const associateSchema: LanguageService["associateSchema"] = (modelURI, schema) =>
    registry.associate(modelURI, schema);
