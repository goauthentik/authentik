/******************************************************************************
 * Copyright 2021 TypeFox GmbH
 * This program and the accompanying materials are made available under the
 * terms of the MIT License, which is available in the project root.
 ******************************************************************************/
import type { DiagnosticSeverity, Range, Diagnostic } from 'vscode-languageserver-types';
import type { LanguageMetaData } from '../languages/language-meta-data.js';
import type { ParseResult } from '../parser/langium-parser.js';
import type { LangiumCoreServices } from '../services.js';
import type { AstNode } from '../syntax-tree.js';
import type { LangiumDocument } from '../workspace/documents.js';
import type { DiagnosticData, DiagnosticInfo, ValidationCategory, ValidationRegistry } from './validation-registry.js';
import { CancellationToken } from '../utils/cancellation.js';
export interface ValidationOptions {
    /**
     * If this is set, only the checks associated with these categories are executed; otherwise
     * all checks are executed. The default category if not specified to the registry is `'fast'`.
     */
    categories?: ValidationCategory[];
    /** If true, no further diagnostics are reported if there are lexing errors. */
    stopAfterLexingErrors?: boolean;
    /** If true, no further diagnostics are reported if there are parsing errors. */
    stopAfterParsingErrors?: boolean;
    /** If true, no further diagnostics are reported if there are linking errors. */
    stopAfterLinkingErrors?: boolean;
}
/**
 * Language-specific service for validating `LangiumDocument`s.
 */
export interface DocumentValidator {
    /**
     * Validates the whole specified document.
     *
     * @param document specified document to validate
     * @param options options to control the validation process
     * @param cancelToken allows to cancel the current operation
     * @throws `OperationCanceled` if a user action occurs during execution
     */
    validateDocument(document: LangiumDocument, options?: ValidationOptions, cancelToken?: CancellationToken): Promise<Diagnostic[]>;
}
export declare class DefaultDocumentValidator implements DocumentValidator {
    protected readonly validationRegistry: ValidationRegistry;
    protected readonly metadata: LanguageMetaData;
    constructor(services: LangiumCoreServices);
    validateDocument(document: LangiumDocument, options?: ValidationOptions, cancelToken?: CancellationToken): Promise<Diagnostic[]>;
    protected processLexingErrors(parseResult: ParseResult, diagnostics: Diagnostic[], _options: ValidationOptions): void;
    protected processParsingErrors(parseResult: ParseResult, diagnostics: Diagnostic[], _options: ValidationOptions): void;
    protected processLinkingErrors(document: LangiumDocument, diagnostics: Diagnostic[], _options: ValidationOptions): void;
    protected validateAst(rootNode: AstNode, options: ValidationOptions, cancelToken?: CancellationToken): Promise<Diagnostic[]>;
    protected toDiagnostic<N extends AstNode>(severity: 'error' | 'warning' | 'info' | 'hint', message: string, info: DiagnosticInfo<N, string>): Diagnostic;
    protected getSource(): string | undefined;
}
export declare function getDiagnosticRange<N extends AstNode>(info: DiagnosticInfo<N, string>): Range;
export declare function toDiagnosticSeverity(severity: 'error' | 'warning' | 'info' | 'hint'): DiagnosticSeverity;
export declare namespace DocumentValidator {
    const LexingError = "lexing-error";
    const ParsingError = "parsing-error";
    const LinkingError = "linking-error";
}
export interface LinkingErrorData extends DiagnosticData {
    containerType: string;
    property: string;
    refText: string;
}
//# sourceMappingURL=document-validator.d.ts.map