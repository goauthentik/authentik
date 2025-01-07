/******************************************************************************
 * Copyright 2022 TypeFox GmbH
 * This program and the accompanying materials are made available under the
 * terms of the MIT License, which is available in the project root.
 ******************************************************************************/
import type { ConfigurationItem, DidChangeConfigurationParams, DidChangeConfigurationRegistrationOptions, InitializeParams, InitializedParams } from 'vscode-languageserver-protocol';
import type { ServiceRegistry } from '../service-registry.js';
import type { LangiumSharedCoreServices } from '../services.js';
import { Deferred } from '../utils/promise-utils.js';
export interface ConfigurationProvider {
    /**
     * A promise that resolves when the configuration provider is ready to be used.
     */
    readonly ready: Promise<void>;
    /**
     * When used in a language server context, this method is called when the server receives
     * the `initialize` request.
     */
    initialize(params: InitializeParams): void;
    /**
     * When used in a language server context, this method is called when the server receives
     * the `initialized` notification.
     */
    initialized(params: ConfigurationInitializedParams): Promise<void>;
    /**
     * Returns a configuration value stored for the given language.
     *
     * @param language The language id
     * @param configuration Configuration name
     */
    getConfiguration(language: string, configuration: string): Promise<any>;
    /**
     *  Updates the cached configurations using the `change` notification parameters.
     *
     * @param change The parameters of a change configuration notification.
     * `settings` property of the change object could be expressed as `Record<string, Record<string, any>>`
     */
    updateConfiguration(change: DidChangeConfigurationParams): void;
}
export interface ConfigurationInitializedParams extends InitializedParams {
    register?: (params: DidChangeConfigurationRegistrationOptions) => void;
    fetchConfiguration?: (configuration: ConfigurationItem[]) => Promise<any>;
}
/**
 * Base configuration provider for building up other configuration providers
 */
export declare class DefaultConfigurationProvider implements ConfigurationProvider {
    protected readonly serviceRegistry: ServiceRegistry;
    protected readonly _ready: Deferred<void>;
    protected settings: Record<string, Record<string, any>>;
    protected workspaceConfig: boolean;
    constructor(services: LangiumSharedCoreServices);
    get ready(): Promise<void>;
    initialize(params: InitializeParams): void;
    initialized(params: ConfigurationInitializedParams): Promise<void>;
    /**
     *  Updates the cached configurations using the `change` notification parameters.
     *
     * @param change The parameters of a change configuration notification.
     * `settings` property of the change object could be expressed as `Record<string, Record<string, any>>`
     */
    updateConfiguration(change: DidChangeConfigurationParams): void;
    protected updateSectionConfiguration(section: string, configuration: any): void;
    /**
    * Returns a configuration value stored for the given language.
    *
    * @param language The language id
    * @param configuration Configuration name
    */
    getConfiguration(language: string, configuration: string): Promise<any>;
    protected toSectionName(languageId: string): string;
}
//# sourceMappingURL=configuration.d.ts.map