export = loader;
/**
 * @this {import("webpack").LoaderContext<LoaderOptions>}
 * @param {string} content
 */
declare function loader(
  this: import("webpack").LoaderContext<MiniCssExtractPlugin.LoaderOptions>,
  content: string
): string | undefined;
declare namespace loader {
  export {
    pitch,
    hotLoader,
    Schema,
    Compiler,
    Compilation,
    Chunk,
    Module,
    Source,
    AssetInfo,
    NormalModule,
    LoaderOptions,
    Locals,
    TODO,
    Dependency,
  };
}
import MiniCssExtractPlugin = require("./index");
/**
 * @this {import("webpack").LoaderContext<LoaderOptions>}
 * @param {string} request
 */
declare function pitch(
  this: import("webpack").LoaderContext<MiniCssExtractPlugin.LoaderOptions>,
  request: string
): void;
/** @typedef {import("schema-utils/declarations/validate").Schema} Schema */
/** @typedef {import("webpack").Compiler} Compiler */
/** @typedef {import("webpack").Compilation} Compilation */
/** @typedef {import("webpack").Chunk} Chunk */
/** @typedef {import("webpack").Module} Module */
/** @typedef {import("webpack").sources.Source} Source */
/** @typedef {import("webpack").AssetInfo} AssetInfo */
/** @typedef {import("webpack").NormalModule} NormalModule */
/** @typedef {import("./index.js").LoaderOptions} LoaderOptions */
/** @typedef {{ [key: string]: string | function }} Locals */
/** @typedef {any} TODO */
/**
 * @typedef {Object} Dependency
 * @property {string} identifier
 * @property {string | null} context
 * @property {Buffer} content
 * @property {string} media
 * @property {string} [supports]
 * @property {string} [layer]
 * @property {Buffer} [sourceMap]
 */
/**
 * @param {string} content
 * @param {{ loaderContext: import("webpack").LoaderContext<LoaderOptions>, options: LoaderOptions, locals: Locals | undefined }} context
 * @returns {string}
 */
declare function hotLoader(
  content: string,
  context: {
    loaderContext: import("webpack").LoaderContext<LoaderOptions>;
    options: LoaderOptions;
    locals: Locals | undefined;
  }
): string;
type Schema = import("schema-utils/declarations/validate").Schema;
type Compiler = import("webpack").Compiler;
type Compilation = import("webpack").Compilation;
type Chunk = import("webpack").Chunk;
type Module = import("webpack").Module;
type Source = import("webpack").sources.Source;
type AssetInfo = import("webpack").AssetInfo;
type NormalModule = import("webpack").NormalModule;
type LoaderOptions = import("./index.js").LoaderOptions;
type Locals = {
  [key: string]: string | Function;
};
type TODO = any;
type Dependency = {
  identifier: string;
  context: string | null;
  content: Buffer;
  media: string;
  supports?: string | undefined;
  layer?: string | undefined;
  sourceMap?: Buffer | undefined;
};
