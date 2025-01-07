/**
 * @typedef {import('vfile').VFileOptions} Options
 * @typedef {import('vfile').VFileValue} Value
 */

/**
 * @typedef {'ascii' | 'base64' | 'base64url' | 'binary' | 'hex' | 'latin1' | 'ucs-2' | 'ucs2' | 'utf-8' | 'utf16le' | 'utf8'} BufferEncoding
 *   Encodings supported by the buffer class.
 *
 *   This is a copy of the types from Node, copied to prevent Node globals from
 *   being needed.
 *   Copied from: <https://github.com/DefinitelyTyped/DefinitelyTyped/blob/1761eec/types/node/buffer.d.ts#L223>.
 *
 * @typedef ReadOptions
 *   Configuration for `fs.readFile`.
 * @property {BufferEncoding | null | undefined} [encoding]
 *   Encoding to read file as, will turn `file.value` into a string if passed.
 * @property {string | undefined} [flag]
 *   File system flags to use.
 *
 * @typedef WriteOptions
 *   Configuration for `fs.writeFile`.
 * @property {BufferEncoding | null | undefined} [encoding]
 *   Encoding to write file as.
 * @property {string | undefined} [flag]
 *   File system flags to use.
 * @property {number | string | undefined} [mode]
 *   File mode (permission and sticky bits) if the file was newly created.
 *
 * @typedef {URL | Value} Path
 *   URL to file or path to file.
 *
 *   > 👉 **Note**: `Value` is used here because it’s a smarter `Buffer`
 * @typedef {Options | Path | VFile} Compatible
 *   URL to file, path to file, options for file, or actual file.
 */

/**
 * @callback Callback
 *   Callback called after reading or writing a file.
 * @param {NodeJS.ErrnoException | undefined} error
 *   Error when reading or writing was not successful.
 * @param {VFile | null | undefined} file
 *   File when reading or writing was successful.
 * @returns {undefined}
 *   Nothing.
 *
 * @callback Resolve
 * @param {VFile} result
 *   File.
 * @returns {void}
 *   Nothing (note: has to be `void` for TSs `Promise` interface).
 *
 * @callback Reject
 * @param {NodeJS.ErrnoException} error
 *   Error.
 * @param {VFile | undefined} [result]
 *   File.
 * @returns {void}
 *   Nothing (note: has to be `void` for TSs `Promise` interface).
 */

import fs from 'node:fs'
import path from 'node:path'
import {VFile} from 'vfile'

// To do: next major: remove `toVFile`, only accept `VFile`s,
// do not return anything.

/**
 * Create a virtual file and read it in, async.
 *
 * @overload
 * @param {Compatible} description
 * @param {BufferEncoding | ReadOptions | null | undefined} options
 * @param {Callback} callback
 * @returns {undefined}
 *
 * @overload
 * @param {Compatible} description
 * @param {Callback} callback
 * @returns {undefined}
 *
 * @overload
 * @param {Compatible} description
 * @param {BufferEncoding | ReadOptions | null | undefined} [options]
 * @returns {Promise<VFile>}
 *
 * @param {Compatible} description
 *   Path to file, file options, or file itself.
 * @param {BufferEncoding | Callback | ReadOptions | null | undefined} [options]
 *   Encoding to use or Node.JS read options.
 * @param {Callback | null | undefined} [callback]
 *   Callback called when done.
 * @returns {Promise<VFile> | undefined}
 *   Nothing when a callback is given, otherwise promise that resolves to given
 *   file or new file.
 */
export function read(description, options, callback) {
  const file = toVFile(description)

  if (!callback && typeof options === 'function') {
    callback = options
    options = undefined
  }

  if (!callback) {
    return new Promise(executor)
  }

  executor(resolve, callback)

  /**
   * @param {VFile} result
   */
  function resolve(result) {
    // @ts-expect-error: `callback` always defined.
    callback(undefined, result)
  }

  /**
   * @param {Resolve} resolve
   * @param {Reject} reject
   * @returns {void}
   *   Nothing (note: has to be `void` for TSs `Promise` interface).
   */
  function executor(resolve, reject) {
    /** @type {string} */
    let fp

    try {
      fp = path.resolve(file.cwd, file.path)
    } catch (error) {
      const exception = /** @type {NodeJS.ErrnoException} */ (error)
      return reject(exception)
    }

    // @ts-expect-error: `options` is not a callback.
    fs.readFile(fp, options, done)

    /**
     * @param {NodeJS.ErrnoException | undefined} error
     * @param {Value} result
     */
    function done(error, result) {
      if (error) {
        reject(error)
      } else {
        file.value = result
        resolve(file)
      }
    }
  }
}

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
export function readSync(description, options) {
  const file = toVFile(description)
  file.value = fs.readFileSync(path.resolve(file.cwd, file.path), options)
  return file
}

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
export function toVFile(description) {
  if (typeof description === 'string' || description instanceof URL) {
    description = {path: description}
  } else if (isUint8Array(description)) {
    description = {path: new TextDecoder().decode(description)}
  }

  return looksLikeAVFile(description) ? description : new VFile(description)
}

/**
 * Create a virtual file and write it, async.
 *
 * @overload
 * @param {Compatible} description
 * @param {BufferEncoding | WriteOptions | null | undefined} options
 * @param {Callback} callback
 * @returns {undefined}
 *
 * @overload
 * @param {Compatible} description
 * @param {Callback} callback
 * @returns {undefined}
 *
 * @overload
 * @param {Compatible} description
 * @param {BufferEncoding | WriteOptions | null | undefined} [options]
 * @returns {Promise<VFile>}
 *
 * @param {Compatible} description
 *   Path to file, file options, or file itself.
 * @param {BufferEncoding | Callback | WriteOptions | null | undefined} [options]
 *   Encoding to use or Node.JS write options.
 * @param {Callback | null | undefined} [callback]
 *   Callback called when done.
 * @returns
 *   Nothing when a callback is given, otherwise promise that resolves to given
 *   file or new file.
 */
export function write(description, options, callback) {
  const file = toVFile(description)

  // Weird, right? Otherwise `fs` doesn’t accept it.
  if (!callback && typeof options === 'function') {
    callback = options
    options = undefined
  }

  if (!callback) {
    return new Promise(executor)
  }

  executor(resolve, callback)

  /**
   * @param {VFile} result
   */
  function resolve(result) {
    // @ts-expect-error: `callback` always defined.
    callback(undefined, result)
  }

  /**
   * @param {Resolve} resolve
   * @param {Reject} reject
   */
  function executor(resolve, reject) {
    /** @type {string} */
    let fp

    try {
      fp = path.resolve(file.cwd, file.path)
    } catch (error) {
      const exception = /** @type {NodeJS.ErrnoException} */ (error)
      return reject(exception)
    }

    // @ts-expect-error: `options` is not a callback.
    fs.writeFile(fp, file.value || '', options || undefined, done)

    /**
     * @param {NodeJS.ErrnoException | undefined} error
     */
    function done(error) {
      if (error) {
        reject(error)
      } else {
        resolve(file)
      }
    }
  }
}

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
export function writeSync(description, options) {
  const file = toVFile(description)
  fs.writeFileSync(path.resolve(file.cwd, file.path), file.value || '', options)
  return file
}

/**
 * Check if something looks like a vfile.
 *
 * @param {Compatible | null | undefined} value
 *   Value.
 * @returns {value is VFile}
 *   Whether `value` looks like a `VFile`.
 */
function looksLikeAVFile(value) {
  return Boolean(
    value &&
      typeof value === 'object' &&
      'message' in value &&
      'messages' in value
  )
}

/**
 * Check whether `value` is an `Uint8Array`.
 *
 * @param {unknown} value
 *   thing.
 * @returns {value is Uint8Array}
 *   Whether `value` is an `Uint8Array`.
 */
function isUint8Array(value) {
  return Boolean(
    value &&
      typeof value === 'object' &&
      'byteLength' in value &&
      'byteOffset' in value
  )
}
