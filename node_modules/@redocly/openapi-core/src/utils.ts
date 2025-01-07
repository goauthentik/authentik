import * as fs from 'fs';
import { extname } from 'path';
import * as minimatch from 'minimatch';
import fetch from 'node-fetch';
import * as pluralize from 'pluralize';
import { parseYaml } from './js-yaml';
import { UserContext } from './walk';
import { env } from './env';
import { logger, colorize } from './logger';
import { HttpResolveConfig } from './config';
import { HttpsProxyAgent } from 'https-proxy-agent';

export { parseYaml, stringifyYaml } from './js-yaml';

export type StackFrame<T> = {
  prev: StackFrame<T> | null;
  value: T;
};

export type Stack<T> = StackFrame<T> | null;
export type StackNonEmpty<T> = StackFrame<T>;
export function pushStack<T, P extends Stack<T> = Stack<T>>(head: P, value: T) {
  return { prev: head, value };
}

export function popStack<T, P extends Stack<T>>(head: P) {
  return head?.prev ?? null;
}

export type BundleOutputFormat = 'json' | 'yml' | 'yaml';

export async function loadYaml<T>(filename: string): Promise<T> {
  const contents = await fs.promises.readFile(filename, 'utf-8');
  return parseYaml(contents) as T;
}

export function isDefined<T>(x: T | undefined): x is T {
  return x !== undefined;
}

export function isPlainObject(value: any): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

export function isEmptyObject(value: any): value is Record<string, unknown> {
  return isPlainObject(value) && Object.keys(value).length === 0;
}

export function isEmptyArray(value: any) {
  return Array.isArray(value) && value.length === 0;
}

export async function readFileFromUrl(url: string, config: HttpResolveConfig) {
  const headers: Record<string, string> = {};
  for (const header of config.headers) {
    if (match(url, header.matches)) {
      headers[header.name] =
        header.envVariable !== undefined ? env[header.envVariable] || '' : header.value;
    }
  }

  const req = await (config.customFetch || fetch)(url, {
    headers: headers,
  });

  if (!req.ok) {
    throw new Error(`Failed to load ${url}: ${req.status} ${req.statusText}`);
  }

  return { body: await req.text(), mimeType: req.headers.get('content-type') };
}

function match(url: string, pattern: string) {
  if (!pattern.match(/^https?:\/\//)) {
    // if pattern doesn't specify protocol directly, do not match against it
    url = url.replace(/^https?:\/\//, '');
  }
  return minimatch(url, pattern);
}

export function pickObjectProps<T extends Record<string, unknown>>(
  object: T,
  keys: Array<string>
): T {
  return Object.fromEntries(
    keys.filter((key: string) => key in object).map((key: string) => [key, object[key]])
  ) as T;
}

export function omitObjectProps<T extends Record<string, unknown>>(
  object: T,
  keys: Array<string>
): T {
  return Object.fromEntries(Object.entries(object).filter(([key]) => !keys.includes(key))) as T;
}

export function splitCamelCaseIntoWords(str: string) {
  const camel = str
    .split(/(?:[-._])|([A-Z][a-z]+)/)
    .filter(isTruthy)
    .map((item) => item.toLocaleLowerCase());
  const caps = str
    .split(/([A-Z]{2,})/)
    .filter((e: string) => e && e === e.toUpperCase())
    .map((item) => item.toLocaleLowerCase());
  return new Set([...camel, ...caps]);
}

export function validateMimeType(
  { type, value }: any,
  { report, location }: UserContext,
  allowedValues: string[]
) {
  const ruleType = type === 'consumes' ? 'request' : 'response';
  if (!allowedValues)
    throw new Error(`Parameter "allowedValues" is not provided for "${ruleType}-mime-type" rule`);
  if (!value[type]) return;

  for (const mime of value[type]) {
    if (!allowedValues.includes(mime)) {
      report({
        message: `Mime type "${mime}" is not allowed`,
        location: location.child(value[type].indexOf(mime)).key(),
      });
    }
  }
}

export function validateMimeTypeOAS3(
  { type, value }: any,
  { report, location }: UserContext,
  allowedValues: string[]
) {
  const ruleType = type === 'consumes' ? 'request' : 'response';
  if (!allowedValues)
    throw new Error(`Parameter "allowedValues" is not provided for "${ruleType}-mime-type" rule`);
  if (!value.content) return;

  for (const mime of Object.keys(value.content)) {
    if (!allowedValues.includes(mime)) {
      report({
        message: `Mime type "${mime}" is not allowed`,
        location: location.child('content').child(mime).key(),
      });
    }
  }
}

export function isSingular(path: string) {
  return pluralize.isSingular(path);
}

export function readFileAsStringSync(filePath: string) {
  return fs.readFileSync(filePath, 'utf-8');
}

export function yamlAndJsonSyncReader<T>(filePath: string): T {
  const content = fs.readFileSync(filePath, 'utf-8');
  return parseYaml(content) as T;
}

export function isPathParameter(pathSegment: string) {
  return pathSegment.startsWith('{') && pathSegment.endsWith('}');
}

/**
 * Convert Windows backslash paths to slash paths: foo\\bar ➔ foo/bar
 */
export function slash(path: string): string {
  const isExtendedLengthPath = /^\\\\\?\\/.test(path);
  if (isExtendedLengthPath) {
    return path;
  }

  return path.replace(/\\/g, '/');
}

export function isNotEmptyObject(obj: any) {
  return !!obj && Object.keys(obj).length > 0;
}

// TODO: use it everywhere
export function isString(value: unknown): value is string {
  return typeof value === 'string';
}

export function isNotString<T>(value: string | T): value is T {
  return !isString(value);
}

export function assignExisting<T>(target: Record<string, T>, obj: Record<string, T>) {
  for (const k of Object.keys(obj)) {
    if (target.hasOwnProperty(k)) {
      target[k] = obj[k];
    }
  }
}

export function getMatchingStatusCodeRange(code: number | string): string {
  return `${code}`.replace(/^(\d)\d\d$/, (_, firstDigit) => `${firstDigit}XX`);
}

export function isCustomRuleId(id: string) {
  return id.includes('/');
}

export function doesYamlFileExist(filePath: string): boolean {
  return (
    (extname(filePath) === '.yaml' || extname(filePath) === '.yml') &&
    fs?.hasOwnProperty?.('existsSync') &&
    fs.existsSync(filePath)
  );
}

export function showWarningForDeprecatedField(
  deprecatedField: string,
  updatedField?: string,
  updatedObject?: string
) {
  logger.warn(
    `The '${colorize.red(deprecatedField)}' field is deprecated. ${
      updatedField
        ? `Use ${colorize.green(getUpdatedFieldName(updatedField, updatedObject))} instead. `
        : ''
    }Read more about this change: https://redocly.com/docs/api-registry/guides/migration-guide-config-file/#changed-properties\n`
  );
}

export function showErrorForDeprecatedField(
  deprecatedField: string,
  updatedField?: string,
  updatedObject?: string
) {
  throw new Error(
    `Do not use '${deprecatedField}' field. ${
      updatedField ? `Use '${getUpdatedFieldName(updatedField, updatedObject)}' instead. ` : ''
    }\n`
  );
}

export type Falsy = undefined | null | false | '' | 0;

export function isTruthy<Truthy>(value: Truthy | Falsy): value is Truthy {
  return !!value;
}

export function identity<T>(value: T): T {
  return value;
}

export function keysOf<T>(obj: T) {
  if (!obj) return [];
  return Object.keys(obj) as (keyof T)[];
}

export function pickDefined<T extends Record<string, unknown>>(
  obj?: T
): Record<string, unknown> | undefined {
  if (!obj) return undefined;
  const res: Record<string, unknown> = {};
  for (const key in obj) {
    if (obj[key] !== undefined) {
      res[key] = obj[key];
    }
  }
  return res;
}

export function nextTick() {
  new Promise((resolve) => {
    setTimeout(resolve);
  });
}

export async function pause(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function getUpdatedFieldName(updatedField: string, updatedObject?: string) {
  return `${typeof updatedObject !== 'undefined' ? `${updatedObject}.` : ''}${updatedField}`;
}

export function getProxyAgent() {
  const proxy = process.env.HTTPS_PROXY || process.env.HTTP_PROXY;
  return proxy ? new HttpsProxyAgent(proxy) : undefined;
}
