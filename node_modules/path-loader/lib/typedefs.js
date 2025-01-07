/**
 * This file contains all type definitions that are purely for documentation purposes.
 */

/**
 * Options used when loading a path.
 *
 * @typedef {object} LoadOptions
 *
 * @property {string} [encoding='utf-8'] - The encoding to use when loading the file *(File loader only)*
 * @property {string} [method=get] - The HTTP method to use for the request *(HTTP loader only)*
 * @property {module:path-loader.PrepareRequestCallback} [prepareRequest] - The callback used to prepare the request *(HTTP loader only)*
 * @property {module:path-loader.ProcessResponseCallback} [processContent] - The callback used to process the response
 *
 * @memberof module:path-loader
 */

/**
 * Callback used to provide access to altering a remote request prior to the request being made.
 *
 * @callback PrepareRequestCallback
 *
 * @param {object} req - The Superagent request object
 * @param {string} location - The location being retrieved
 * @param {function} callback - First callback
 *
 * @memberof module:path-loader
 */

 /**
  * Callback used to provide access to processing the raw response of the request being made. *(HTTP loader only)*
  *
  * @callback ProcessResponseCallback
  *
  * @param {object} res - The Superagent response object *(For non-HTTP loaders, this object will be like the Superagent
  * object in that it will have a `text` property whose value is the raw string value being processed.  This was done
  * for consistency.  There will also be a `location` property containing the location of the path being loaded.)*
  * @param {function} callback - Error-first callback
  *
  * @returns {*} the result of processing the responses
 *
 * @memberof module:path-loader
  */
