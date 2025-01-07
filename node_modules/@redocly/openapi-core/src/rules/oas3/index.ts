import { Oas3RuleSet } from '../../oas-types';
import { Spec } from '../common/spec';
import { Operation2xxResponse } from '../common/operation-2xx-response';
import { Operation4xxResponse } from '../common/operation-4xx-response';
import { Assertions } from '../common/assertions';
import { OperationIdUnique } from '../common/operation-operationId-unique';
import { OperationParametersUnique } from '../common/operation-parameters-unique';
import { PathParamsDefined } from '../common/path-params-defined';
import { OperationTagDefined } from '../common/operation-tag-defined';
import { NoExampleValueAndExternalValue } from './no-example-value-and-externalValue';
import { NoEnumTypeMismatch } from '../common/no-enum-type-mismatch';
import { NoPathTrailingSlash } from '../common/no-path-trailing-slash';
import { PathDeclarationMustExist } from '../common/path-declaration-must-exist';
import { OperationIdUrlSafe } from '../common/operation-operationId-url-safe';
import { TagsAlphabetical } from '../common/tags-alphabetical';
import { NoServerExample } from './no-server-example.com';
import { NoServerTrailingSlash } from './no-server-trailing-slash';
import { TagDescription } from '../common/tag-description';
import { InfoContact } from '../common/info-contact';
import { InfoLicense } from '../common/info-license';
import { InfoLicenseUrl } from '../common/info-license-url';
import { OperationDescription } from '../common/operation-description';
import { NoUnusedComponents } from './no-unused-components';
import { PathNotIncludeQuery } from '../common/path-not-include-query';
import { ParameterDescription } from '../common/parameter-description';
import { OperationSingularTag } from '../common/operation-singular-tag';
import { SecurityDefined } from '../common/security-defined';
import { NoUnresolvedRefs } from '../no-unresolved-refs';
import { BooleanParameterPrefixes } from './boolean-parameter-prefixes';
import { PathsKebabCase } from '../common/paths-kebab-case';
import { PathHttpVerbsOrder } from '../common/path-http-verbs-order';
import { NoEmptyServers } from './no-empty-servers';
import { ValidContentExamples } from './no-invalid-media-type-examples';
import { NoIdenticalPaths } from '../common/no-identical-paths';
import { NoUndefinedServerVariable } from './no-undefined-server-variable';
import { OperationOperationId } from '../common/operation-operationId';
import { OperationSummary } from '../common/operation-summary';
import { NoAmbiguousPaths } from '../common/no-ambiguous-paths';
import { NoServerVariablesEmptyEnum } from './no-server-variables-empty-enum';
import { NoHttpVerbsInPaths } from '../common/no-http-verbs-in-paths';
import { RequestMimeType } from './request-mime-type';
import { ResponseMimeType } from './response-mime-type';
import { PathSegmentPlural } from '../common/path-segment-plural';
import { PathExcludesPatterns } from '../common/path-excludes-patterns';
import { NoInvalidSchemaExamples } from '../common/no-invalid-schema-examples';
import { NoInvalidParameterExamples } from '../common/no-invalid-parameter-examples';
import { ResponseContainsHeader } from '../common/response-contains-header';
import { ResponseContainsProperty } from './response-contains-property';
import { ScalarPropertyMissingExample } from '../common/scalar-property-missing-example';
import { SpecComponentsInvalidMapName } from './spec-components-invalid-map-name';
import { Operation4xxProblemDetailsRfc7807 } from './operation-4xx-problem-details-rfc7807';
import { RequiredStringPropertyMissingMinLength } from '../common/required-string-property-missing-min-length';
import { SpecStrictRefs } from '../common/spec-strict-refs';
import { ComponentNameUnique } from './component-name-unique';
import { ArrayParameterSerialization } from './array-parameter-serialization';
import { NoRequiredSchemaPropertiesUndefined } from '../common/no-required-schema-properties-undefined';

export const rules: Oas3RuleSet<'built-in'> = {
  spec: Spec,
  'info-contact': InfoContact,
  'info-license': InfoLicense,
  'info-license-url': InfoLicenseUrl,
  'operation-2xx-response': Operation2xxResponse,
  'operation-4xx-response': Operation4xxResponse,
  'operation-4xx-problem-details-rfc7807': Operation4xxProblemDetailsRfc7807,
  assertions: Assertions,
  'operation-operationId-unique': OperationIdUnique,
  'operation-parameters-unique': OperationParametersUnique,
  'operation-tag-defined': OperationTagDefined,
  'no-example-value-and-externalValue': NoExampleValueAndExternalValue,
  'no-enum-type-mismatch': NoEnumTypeMismatch,
  'no-path-trailing-slash': NoPathTrailingSlash,
  'no-empty-servers': NoEmptyServers,
  'path-declaration-must-exist': PathDeclarationMustExist,
  'operation-operationId-url-safe': OperationIdUrlSafe,
  'operation-operationId': OperationOperationId,
  'operation-summary': OperationSummary,
  'tags-alphabetical': TagsAlphabetical,
  'no-server-example.com': NoServerExample,
  'no-server-trailing-slash': NoServerTrailingSlash,
  'tag-description': TagDescription,
  'operation-description': OperationDescription,
  'no-unused-components': NoUnusedComponents,
  'path-not-include-query': PathNotIncludeQuery,
  'path-parameters-defined': PathParamsDefined,
  'path-params-defined': PathParamsDefined,
  'parameter-description': ParameterDescription,
  'operation-singular-tag': OperationSingularTag,
  'security-defined': SecurityDefined,
  'no-unresolved-refs': NoUnresolvedRefs,
  'paths-kebab-case': PathsKebabCase,
  'boolean-parameter-prefixes': BooleanParameterPrefixes,
  'path-http-verbs-order': PathHttpVerbsOrder,
  'no-invalid-media-type-examples': ValidContentExamples,
  'no-identical-paths': NoIdenticalPaths,
  'no-ambiguous-paths': NoAmbiguousPaths,
  'no-undefined-server-variable': NoUndefinedServerVariable,
  'no-server-variables-empty-enum': NoServerVariablesEmptyEnum,
  'no-http-verbs-in-paths': NoHttpVerbsInPaths,
  'path-excludes-patterns': PathExcludesPatterns,
  'request-mime-type': RequestMimeType,
  'response-mime-type': ResponseMimeType,
  'path-segment-plural': PathSegmentPlural,
  'no-invalid-schema-examples': NoInvalidSchemaExamples,
  'no-invalid-parameter-examples': NoInvalidParameterExamples,
  'response-contains-header': ResponseContainsHeader,
  'response-contains-property': ResponseContainsProperty,
  'scalar-property-missing-example': ScalarPropertyMissingExample,
  'spec-components-invalid-map-name': SpecComponentsInvalidMapName,
  'required-string-property-missing-min-length': RequiredStringPropertyMissingMinLength,
  'spec-strict-refs': SpecStrictRefs,
  'component-name-unique': ComponentNameUnique,
  'array-parameter-serialization': ArrayParameterSerialization,
  'no-required-schema-properties-undefined': NoRequiredSchemaPropertiesUndefined,
};

export const preprocessors = {};
