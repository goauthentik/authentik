/******************************************************************************
 * Copyright 2021 TypeFox GmbH
 * This program and the accompanying materials are made available under the
 * terms of the MIT License, which is available in the project root.
 ******************************************************************************/
import { UriUtils } from './utils/uri-utils.js';
/**
 * Generic registry for Langium services, but capable of being used with extending service sets as well (such as the lsp-complete LangiumCoreServices set)
 */
export class DefaultServiceRegistry {
    register(language) {
        if (!this.singleton && !this.map) {
            // This is the first language to be registered; store it as singleton.
            this.singleton = language;
            return;
        }
        if (!this.map) {
            this.map = {};
            if (this.singleton) {
                // Move the previous singleton instance to the new map.
                for (const ext of this.singleton.LanguageMetaData.fileExtensions) {
                    this.map[ext] = this.singleton;
                }
                this.singleton = undefined;
            }
        }
        // Store the language services in the map.
        for (const ext of language.LanguageMetaData.fileExtensions) {
            if (this.map[ext] !== undefined && this.map[ext] !== language) {
                console.warn(`The file extension ${ext} is used by multiple languages. It is now assigned to '${language.LanguageMetaData.languageId}'.`);
            }
            this.map[ext] = language;
        }
    }
    getServices(uri) {
        if (this.singleton !== undefined) {
            return this.singleton;
        }
        if (this.map === undefined) {
            throw new Error('The service registry is empty. Use `register` to register the services of a language.');
        }
        const ext = UriUtils.extname(uri);
        const services = this.map[ext];
        if (!services) {
            throw new Error(`The service registry contains no services for the extension '${ext}'.`);
        }
        return services;
    }
    get all() {
        if (this.singleton !== undefined) {
            return [this.singleton];
        }
        if (this.map !== undefined) {
            return Object.values(this.map);
        }
        return [];
    }
}
//# sourceMappingURL=service-registry.js.map