/**
 * @file Associates editor models with the JSON Schemas their language services validate against.
 */

import type { CodeEditorSchema } from "#elements/CodeEditor/shared";

/**
 * A schema as the JSON and YAML language services take it.
 */
export interface SchemaAssociation {
    /**
     * Where the schema is fetched from, or a unique ID when it is given inline.
     */
    uri: string;
    /**
     * The models the schema applies to.
     */
    fileMatch: string[];
    /**
     * The schema itself, when given inline.
     */
    schema?: object;
}

export interface Disposable {
    dispose(): void;
}

let inlineSchemaCount = 0;

/**
 * The schemas of one language's models.
 */
export class SchemaRegistry {
    #schemas = new Map<string, CodeEditorSchema>();
    #inlineURIs = new WeakMap<object, string>();
    #listeners = new Set<() => void>();

    /**
     * Applies the schema to the model until the returned disposable is disposed.
     */
    public associate(modelURI: string, schema: CodeEditorSchema): Disposable {
        this.#schemas.set(modelURI, schema);
        this.#notify();

        return {
            dispose: () => {
                if (this.#schemas.get(modelURI) !== schema) return;

                this.#schemas.delete(modelURI);
                this.#notify();
            },
        };
    }

    public toAssociations(): SchemaAssociation[] {
        return Array.from(this.#schemas, ([modelURI, schema]) => {
            if (typeof schema === "string") {
                // Language services fetch from their own context, such as a worker's URL.
                return { uri: new URL(schema, document.baseURI).href, fileMatch: [modelURI] };
            }

            return { uri: this.#inlineURI(schema), fileMatch: [modelURI], schema };
        });
    }

    /**
     * Calls the listener whenever an association is added or removed.
     */
    public onDidChange(listener: () => void): Disposable {
        this.#listeners.add(listener);

        return { dispose: () => this.#listeners.delete(listener) };
    }

    #inlineURI(schema: object): string {
        let uri = this.#inlineURIs.get(schema);

        if (!uri) {
            uri = `inmemory://ak-code-editor/schemas/${++inlineSchemaCount}.json`;
            this.#inlineURIs.set(schema, uri);
        }

        return uri;
    }

    #notify() {
        for (const listener of this.#listeners) listener();
    }
}
