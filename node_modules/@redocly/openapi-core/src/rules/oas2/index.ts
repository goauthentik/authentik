import { Oas2Rule } from '../../visitors';
import { Spec } from '../common/spec';
import { NoInvalidSchemaExamples } from '../common/no-invalid-schema-examples';
import { NoInvalidParameterExamples } from '../common/no-invalid-parameter-examples';
import { InfoContact } from '../common/info-contact';
import { InfoLicense } from '../common/info-license';
import { InfoLicenseUrl } from '../common/info-license-url';
import { BooleanParameterPrefixes } from './boolean-parameter-prefixes';
import { TagDescription } from '../common/tag-description';
import { TagsAlphabetical } from '../common/tags-alphabetical';
import { PathsKebabCase } from '../common/paths-kebab-case';
import { NoEnumTypeMismatch } from '../common/no-enum-type-mismatch';
import { NoPathTrailingSlash } from '../common/no-path-trailing-slash';
import { Operation2xxResponse } from '../common/operation-2xx-response';
import { Operation4xxResponse } from '../common/operation-4xx-response';
import { Assertions } from '../common/assertions';
import { OperationIdUnique } from '../common/operation-operationId-unique';
import { OperationParametersUnique } from '../common/operation-parameters-unique';
import { PathParamsDefined } from '../common/path-params-defined';
import { OperationTagDefined } from '../common/operation-tag-defined';
import { PathDeclarationMustExist } from '../common/path-declaration-must-exist';
import { OperationIdUrlSafe } from '../common/operation-operationId-url-safe';
import { OperationDescription } from '../common/operation-description';
import { PathNotIncludeQuery } from '../common/path-not-include-query';
import { ParameterDescription } from '../common/parameter-description';
import { OperationSingularTag } from '../common/operation-singular-tag';
import { SecurityDefined } from '../common/security-defined';
import { NoUnresolvedRefs } from '../no-unresolved-refs';
import { PathHttpVerbsOrder } from '../common/path-http-verbs-order';
import { NoIdenticalPaths } from '../common/no-identical-paths';
import { OperationOperationId } from '../common/operation-operationId';
import { OperationSummary } from '../common/operation-summary';
import { NoAmbiguousPaths } from '../common/no-ambiguous-paths';
import { NoHttpVerbsInPaths } from '../common/no-http-verbs-in-paths';
import { PathExcludesPatterns } from '../common/path-excludes-patterns';
import { RequestMimeType } from './request-mime-type';
import { ResponseMimeType } from './response-mime-type';
import { PathSegmentPlural } from '../common/path-segment-plural';
import { ResponseContainsHeader } from '../common/response-contains-header';
import { ResponseContainsProperty } from './response-contains-property';
import { ScalarPropertyMissingExample } from '../common/scalar-property-missing-example';
import { RequiredStringPropertyMissingMinLength } from '../common/required-string-property-missing-min-length';
import { SpecStrictRefs } from '../common/spec-strict-refs';
import { NoRequiredSchemaPropertiesUndefined } from '../common/no-required-schema-properties-undefined';

import type { Oas2RuleSet } from 'core/src/oas-types';

export const rules: Oas2RuleSet<'built-in'> = {
  spec: Spec as Oas2Rule,
  'no-invalid-schema-examples': NoInvalidSchemaExamples,
  'no-invalid-parameter-examples': NoInvalidParameterExamples,
  'info-contact': InfoContact as Oas2Rule,
  'info-license': InfoLicense as Oas2Rule,
  'info-license-url': InfoLicenseUrl as Oas2Rule,
  'tag-description': TagDescription as Oas2Rule,
  'tags-alphabetical': TagsAlphabetical as Oas2Rule,
  'paths-kebab-case': PathsKebabCase as Oas2Rule,
  'no-enum-type-mismatch': NoEnumTypeMismatch as Oas2Rule,
  'boolean-parameter-prefixes': BooleanParameterPrefixes as Oas2Rule,
  'no-path-trailing-slash': NoPathTrailingSlash as Oas2Rule,
  'operation-2xx-response': Operation2xxResponse as Oas2Rule,
  'operation-4xx-response': Operation4xxResponse as Oas2Rule,
  assertions: Assertions as Oas2Rule,
  'operation-operationId-unique': OperationIdUnique as Oas2Rule,
  'operation-parameters-unique': OperationParametersUnique as Oas2Rule,
  'path-parameters-defined': PathParamsDefined as Oas2Rule,
  'operation-tag-defined': OperationTagDefined as Oas2Rule,
  'path-declaration-must-exist': PathDeclarationMustExist as Oas2Rule,
  'operation-operationId-url-safe': OperationIdUrlSafe as Oas2Rule,
  'operation-operationId': OperationOperationId as Oas2Rule,
  'operation-summary': OperationSummary as Oas2Rule,
  'operation-description': OperationDescription as Oas2Rule,
  'path-not-include-query': PathNotIncludeQuery as Oas2Rule,
  'path-params-defined': PathParamsDefined as Oas2Rule,
  'parameter-description': ParameterDescription as Oas2Rule,
  'operation-singular-tag': OperationSingularTag as Oas2Rule,
  'security-defined': SecurityDefined as Oas2Rule,
  'no-unresolved-refs': NoUnresolvedRefs as Oas2Rule,
  'no-identical-paths': NoIdenticalPaths as Oas2Rule,
  'no-ambiguous-paths': NoAmbiguousPaths as Oas2Rule,
  'path-http-verbs-order': PathHttpVerbsOrder as Oas2Rule,
  'no-http-verbs-in-paths': NoHttpVerbsInPaths as Oas2Rule,
  'path-excludes-patterns': PathExcludesPatterns as Oas2Rule,
  'request-mime-type': RequestMimeType as Oas2Rule,
  'response-mime-type': ResponseMimeType as Oas2Rule,
  'path-segment-plural': PathSegmentPlural as Oas2Rule,
  'response-contains-header': ResponseContainsHeader as Oas2Rule,
  'response-contains-property': ResponseContainsProperty as Oas2Rule,
  'scalar-property-missing-example': ScalarPropertyMissingExample,
  'required-string-property-missing-min-length': RequiredStringPropertyMissingMinLength,
  'spec-strict-refs': SpecStrictRefs,
  'no-required-schema-properties-undefined': NoRequiredSchemaPropertiesUndefined,
};

export const preprocessors = {};
