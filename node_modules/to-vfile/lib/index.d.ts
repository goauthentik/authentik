export function read(
  description: Compatible,
  options: BufferEncoding | ReadOptions | null | undefined,
  callback: Callback
): undefined
export function read(description: Compatible, callback: Callback): undefined
export function read(
  description: Compatible,
  options?: BufferEncoding | ReadOptions | null | undefined
): Promise<VFile>
/**
 * Create a virtual file and read it in, synchronously.
 *
 * @param {Compatible} description
 *   Path to file, file options, or file itself.
 * @param {BufferEncoding | ReadOptions | null | undefined} [options]
 *   Encoding to use or Node.JS read options.
 * @returns {VFile}
 *   Given file or new file.
 */
export function readSync(
  description: Compatible,
  options?: BufferEncoding | ReadOptions | null | undefined
): VFile
/**
 * Create a virtual file from a description.
 *
 * This is like `VFile`, but it accepts a file path instead of file contents.
 *
 * If `options` is a string, URL, or buffer, it’s used as the path.
 * Otherwise, if it’s a file, that’s returned instead.
 * Otherwise, the options are passed through to `new VFile()`.
 *
 * @param {Compatible | null | undefined} [description]
 *   Path to file, file options, or file itself.
 * @returns {VFile}
 *   Given file or new file.
 */
export function toVFile(description?: Compatible | null | undefined): VFile
export function write(
  description: Compatible,
  options: BufferEncoding | WriteOptions | null | undefined,
  callback: Callback
): undefined
export function write(description: Compatible, callback: Callback): undefined
export function write(
  description: Compatible,
  options?: BufferEncoding | WriteOptions | null | undefined
): Promise<VFile>
/**
 * Create a virtual file and write it, synchronously.
 *
 * @param {Compatible} description
 *   Path to file, file options, or file itself.
 * @param {BufferEncoding | WriteOptions | null | undefined} [options]
 *   Encoding to use or Node.JS write options.
 * @returns {VFile}
 *   Given file or new file.
 */
export function writeSync(
  description: Compatible,
  options?: BufferEncoding | WriteOptions | null | undefined
): VFile
export type Options = import('vfile').VFileOptions
export type Value = import('vfile').VFileValue
/**
 * Encodings supported by the buffer class.
 *
 * This is a copy of the types from Node, copied to prevent Node globals from
 * being needed.
 * Copied from: <https://github.com/DefinitelyTyped/DefinitelyTyped/blob/1761eec/types/node/buffer.d.ts#L223>.
 */
export type BufferEncoding =
  | 'ascii'
  | 'base64'
  | 'base64url'
  | 'binary'
  | 'hex'
  | 'latin1'
  | 'ucs-2'
  | 'ucs2'
  | 'utf-8'
  | 'utf16le'
  | 'utf8'
/**
 * Configuration for `fs.readFile`.
 */
export type ReadOptions = {
  /**
   * Encoding to read file as, will turn `file.value` into a string if passed.
   */
  encoding?: BufferEncoding | null | undefined
  /**
   * File system flags to use.
   */
  flag?: string | undefined
}
/**
 * Configuration for `fs.writeFile`.
 */
export type WriteOptions = {
  /**
   * Encoding to write file as.
   */
  encoding?: BufferEncoding | null | undefined
  /**
   * File system flags to use.
   */
  flag?: string | undefined
  /**
   * File mode (permission and sticky bits) if the file was newly created.
   */
  mode?: number | string | undefined
}
/**
 * URL to file or path to file.
 *
 * > 👉 **Note**: `Value` is used here because it’s a smarter `Buffer`
 */
export type Path = URL | Value
/**
 * URL to file, path to file, options for file, or actual file.
 */
export type Compatible = Options | Path | VFile
/**
 * Callback called after reading or writing a file.
 */
export type Callback = (
  error: NodeJS.ErrnoException | undefined,
  file: VFile | null | undefined
) => undefined
export type Resolve = (result: VFile) => void
export type Reject = (
  error: NodeJS.ErrnoException,
  result?: VFile | undefined
) => void
import {VFile} from 'vfile'
