/**
 * @remarks
 *   Runs Monaco's JSON language service on the page instead of in a web worker, as the CSS
 *   service does.
 * @file JSON highlighting, and suggestions, hovers and validation from the editor's schema.
 */

import { PageWorkerContext } from "#elements/CodeEditor/languages/page-worker";
import { SchemaRegistry } from "#elements/CodeEditor/languages/schemas";
import type { LanguageService } from "#elements/CodeEditor/languages/types";

import { languages } from "monaco-editor/editor/editor.api";
import {
    CompletionAdapter,
    DiagnosticsAdapter,
    FoldingRangeAdapter,
    HoverAdapter,
} from "monaco-editor/languages/features/common/lspLanguageFeatures";
import { JSONWorker } from "monaco-editor/languages/features/json/jsonWorker";
import { createTokenizationSupport } from "monaco-editor/languages/features/json/tokenization";

const registry = new SchemaRegistry();

function createService() {
    return new JSONWorker(PageWorkerContext, {
        languageId: "json",
        enableSchemaRequest: true,
        languageSettings: {
            validate: true,
            allowComments: false,
            schemas: registry.toAssociations(),
        },
    });
}

let service = createService();

// The service reads its schemas once, so a new set takes a new service.
registry.onDidChange(() => {
    service = createService();
});

const worker = () => Promise.resolve(service);

languages.setTokensProvider("json", createTokenizationSupport(false));

languages.setLanguageConfiguration("json", {
    wordPattern: /(-?\d*\.\d\w*)|([^[{\]}:",\s]+)/g,
    brackets: [
        ["{", "}"],
        ["[", "]"],
    ],
    autoClosingPairs: [
        { open: "{", close: "}", notIn: ["string"] },
        { open: "[", close: "]", notIn: ["string"] },
        { open: '"', close: '"', notIn: ["string"] },
    ],
});

languages.registerCompletionItemProvider("json", new CompletionAdapter(worker, [" ", ":", '"']));
languages.registerHoverProvider("json", new HoverAdapter(worker));
languages.registerFoldingRangeProvider("json", new FoldingRangeAdapter(worker));

new DiagnosticsAdapter("json", worker, (listener) => {
    // The adapter only checks models created after it, so check the existing ones once.
    queueMicrotask(listener);

    return registry.onDidChange(listener);
});

export const associateSchema: LanguageService["associateSchema"] = (modelURI, schema) =>
    registry.associate(modelURI, schema);
