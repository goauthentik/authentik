/*
 * The MIT License (MIT)
 *
 * Copyright (c) 2014 Jeremy Whitlock
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

'use strict';

var _ = require('lodash');
var gl = require('graphlib');
var path = require('path');
var PathLoader = require('path-loader');
var qs = require('querystring');
var slash = require('slash');
var URI = require('uri-js');

var badPtrTokenRegex = /~(?:[^01]|$)/g;
var remoteCache = {};
var remoteTypes = ['relative', 'remote'];
var remoteUriTypes = ['absolute', 'uri'];
var uriDetailsCache = {};

// Load promises polyfill if necessary
/* istanbul ignore if */
if (typeof Promise === 'undefined') {
  require('native-promise-only');
}

/* Internal Functions */

function combineQueryParams (qs1, qs2) {
  var combined = {};

  function mergeQueryParams (obj) {
    _.forOwn(obj, function (val, key) {
      combined[key] = val;
    });
  }

  mergeQueryParams(qs.parse(qs1 || ''));
  mergeQueryParams(qs.parse(qs2 || ''));

  return Object.keys(combined).length === 0 ? undefined : qs.stringify(combined);
}

function combineURIs (u1, u2) {
  // Convert Windows paths
  if (_.isString(u1)) {
    u1 = slash(u1);
  }

  if (_.isString(u2)) {
    u2 = slash(u2);
  }

  var u2Details = parseURI(_.isUndefined(u2) ? '' : u2);
  var u1Details;
  var combinedDetails;

  if (remoteUriTypes.indexOf(u2Details.reference) > -1) {
    combinedDetails = u2Details;
  } else {
    u1Details = _.isUndefined(u1) ? undefined : parseURI(u1);

    if (!_.isUndefined(u1Details)) {
      combinedDetails = u1Details;

      // Join the paths
      combinedDetails.path = slash(path.join(u1Details.path, u2Details.path));

      // Join query parameters
      combinedDetails.query = combineQueryParams(u1Details.query, u2Details.query);
    } else {
      combinedDetails = u2Details;
    }
  }

  // Remove the fragment
  combinedDetails.fragment = undefined;

  // For relative URIs, add back the '..' since it was removed above
  return (remoteUriTypes.indexOf(combinedDetails.reference) === -1 &&
          combinedDetails.path.indexOf('../') === 0 ? '../' : '') + URI.serialize(combinedDetails);
}

function findAncestors (obj, path) {
  var ancestors = [];
  var node;

  if (path.length > 0) {
    node = obj;

    path.slice(0, path.length - 1).forEach(function (seg) {
      if (seg in node) {
        node = node[seg];

        ancestors.push(node);
      }
    });
  }

  return ancestors;
}

function isRemote (refDetails) {
  return remoteTypes.indexOf(getRefType(refDetails)) > -1;
}

function isValid (refDetails) {
  return _.isUndefined(refDetails.error) && refDetails.type !== 'invalid';
}

function findValue (obj, path) {
  var value = obj;

  // Using this manual approach instead of _.get since we have to decodeURI the segments
  path.forEach(function (seg) {
    if (seg in value) {
      value = value[seg];
    } else {
      throw Error('JSON Pointer points to missing location: ' + pathToPtr(path));
    }
  });

  return value;
}

function getExtraRefKeys (ref) {
  return Object.keys(ref).filter(function (key) {
    return key !== '$ref';
  });
}

function getRefType (refDetails) {
  var type;

  // Convert the URI reference to one of our types
  switch (refDetails.uriDetails.reference) {
  case 'absolute':
  case 'uri':
    type = 'remote';
    break;
  case 'same-document':
    type = 'local';
    break;
  default:
    type = refDetails.uriDetails.reference;
  }

  return type;
}

function getRemoteDocument (url, options) {
  var cacheEntry = remoteCache[url];
  var allTasks = Promise.resolve();
  var loaderOptions = _.cloneDeep(options.loaderOptions || {});

  if (_.isUndefined(cacheEntry)) {
    // If there is no content processor, default to processing the raw response as JSON
    if (_.isUndefined(loaderOptions.processContent)) {
      loaderOptions.processContent = function (res, callback) {
        callback(undefined, JSON.parse(res.text));
      };
    }

    // Attempt to load the resource using path-loader
    allTasks = PathLoader.load(decodeURI(url), loaderOptions);

    // Update the cache
    allTasks = allTasks
      .then(function (res) {
        remoteCache[url] = {
          value: res
        };

        return res;
      })
      .catch(function (err) {
        remoteCache[url] = {
          error: err
        };

        throw err;
      });
  } else {
    // Return the cached version
    allTasks = allTasks.then(function () {
      if (_.isError(cacheEntry.error)) {
        throw cacheEntry.error;
      } else {
        return cacheEntry.value;
      }
    });
  }

  // Return a cloned version to avoid updating the cache
  allTasks = allTasks.then(function (res) {
    return _.cloneDeep(res);
  });

  return allTasks;
}

function isRefLike (obj, throwWithDetails) {
  var refLike = true;

  try {
    if (!_.isPlainObject(obj)) {
      throw new Error('obj is not an Object');
    } else if (!_.isString(obj.$ref)) {
      throw new Error('obj.$ref is not a String');
    }
  } catch (err) {
    if (throwWithDetails) {
      throw err;
    }

    refLike = false;
  }

  return refLike;
}

function makeAbsolute (location) {
  if (location.indexOf('://') === -1 && !path.isAbsolute(location)) {
    return path.resolve(process.cwd(), location);
  } else {
    return location;
  }
}

function makeRefFilter (options) {
  var refFilter;
  var validTypes;

  if (_.isArray(options.filter) || _.isString(options.filter)) {
    validTypes = _.isString(options.filter) ? [options.filter] : options.filter;
    refFilter = function (refDetails) {
      // Check the exact type or for invalid URIs, check its original type
      return validTypes.indexOf(refDetails.type) > -1 || validTypes.indexOf(getRefType(refDetails)) > -1;
    };
  } else if (_.isFunction(options.filter)) {
    refFilter = options.filter;
  } else if (_.isUndefined(options.filter)) {
    refFilter = function () {
      return true;
    };
  }

  return function (refDetails, path) {
    return (refDetails.type !== 'invalid' || options.includeInvalid === true) && refFilter(refDetails, path);
  };
}

function makeSubDocPath (options) {
  var subDocPath;

  if (_.isArray(options.subDocPath)) {
    subDocPath = options.subDocPath;
  } else if (_.isString(options.subDocPath)) {
    subDocPath = pathFromPtr(options.subDocPath);
  } else if (_.isUndefined(options.subDocPath)) {
    subDocPath = [];
  }

  return subDocPath;
}

function markMissing (refDetails, err) {
  refDetails.error = err.message;
  refDetails.missing = true;
}

function parseURI (uri) {
  // We decode first to avoid doubly encoding
  return URI.parse(uri);
}

function buildRefModel (document, options, metadata) {
  var allTasks = Promise.resolve();
  var subDocPtr = pathToPtr(options.subDocPath);
  var absLocation = makeAbsolute(options.location);
  var relativeBase = path.dirname(options.location);
  var docDepKey = absLocation + subDocPtr;
  var refs;
  var rOptions;

  // Store the document in the metadata if necessary
  if (_.isUndefined(metadata.docs[absLocation])) {
    metadata.docs[absLocation] = document;
  }

  // If there are no dependencies stored for the location+subDocPath, we've never seen it before and will process it
  if (_.isUndefined(metadata.deps[docDepKey])) {
    metadata.deps[docDepKey] = {};

    // Find the references based on the options
    refs = findRefs(document, options);

    // Iterate over the references and process
    _.forOwn(refs, function (refDetails, refPtr) {
      var refKey = makeAbsolute(options.location) + refPtr;
      var refdKey = refDetails.refdId = decodeURI(makeAbsolute(isRemote(refDetails) ?
                                                       combineURIs(relativeBase, refDetails.uri) :
                                                       options.location) + '#' +
                                          (refDetails.uri.indexOf('#') > -1 ?
                                             refDetails.uri.split('#')[1] :
                                             ''));

      // Record reference metadata
      metadata.refs[refKey] = refDetails;

      // Do not process invalid references
      if (!isValid(refDetails)) {
        return;
      }

      // Record the fully-qualified URI
      refDetails.fqURI = refdKey;

      // Record dependency (relative to the document's sub-document path)
      metadata.deps[docDepKey][refPtr === subDocPtr ? '#' : refPtr.replace(subDocPtr + '/', '#/')] = refdKey;

      // Do not process directly-circular references (to an ancestor or self)
      if (refKey.indexOf(refdKey + '/') === 0 || refKey === refdKey) {
        refDetails.circular = true;

        return;
      }

      // Prepare the options for subsequent processDocument calls
      rOptions = _.cloneDeep(options);

      rOptions.subDocPath = _.isUndefined(refDetails.uriDetails.fragment) ?
                                     [] :
                                     pathFromPtr(decodeURI(refDetails.uriDetails.fragment));

      // Resolve the reference
      if (isRemote(refDetails)) {
        // Delete filter.options because all remote references should be fully resolved
        delete rOptions.filter;
        // The new location being referenced
        rOptions.location = refdKey.split('#')[0];

        allTasks = allTasks
          .then(function (nMetadata, nOptions) {
            return function () {
              var rAbsLocation = makeAbsolute(nOptions.location);
              var rDoc = nMetadata.docs[rAbsLocation];

              if (_.isUndefined(rDoc)) {
                // We have no cache so we must retrieve the document
                return getRemoteDocument(rAbsLocation, nOptions)
                        .catch(function (err) {
                          // Store the response in the document cache
                          nMetadata.docs[rAbsLocation] = err;

                          // Return the error to allow the subsequent `then` to handle both errors and successes
                          return err;
                        });
              } else {
                // We have already retrieved (or attempted to) the document and should use the cached version in the
                // metadata since it could already be processed some.
                return Promise.resolve()
                  .then(function () {
                    return rDoc;
                  });
              }
            };
          }(metadata, rOptions));
      } else {
        allTasks = allTasks
          .then(function () {
            return document;
          });
      }

      // Process the remote document or the referenced portion of the local document
      allTasks = allTasks
        .then(function (nMetadata, nOptions, nRefDetails) {
          return function (doc) {
            if (_.isError(doc)) {
              markMissing(nRefDetails, doc);
            } else {
              // Wrapped in a try/catch since findRefs throws
              try {
                return buildRefModel(doc, nOptions, nMetadata)
                  .catch(function (err) {
                    markMissing(nRefDetails, err);
                  });
              } catch (err) {
                markMissing(nRefDetails, err);
              }
            }
          };
        }(metadata, rOptions, refDetails));
    });
  }

  return allTasks;
}

function setValue (obj, refPath, value) {
  findValue(obj, refPath.slice(0, refPath.length - 1))[refPath[refPath.length - 1]] = value;
}

function walk (ancestors, node, path, fn) {
  var processChildren = true;

  function walkItem (item, segment) {
    path.push(segment);
    walk(ancestors, item, path, fn);
    path.pop();
  }

  // Call the iteratee
  if (_.isFunction(fn)) {
    processChildren = fn(ancestors, node, path);
  }

  // We do not process circular objects again
  if (ancestors.indexOf(node) === -1) {
    ancestors.push(node);

    if (processChildren !== false) {
      if (_.isArray(node)) {
        node.forEach(function (member, index) {
          walkItem(member, index.toString());
        });
      } else if (_.isObject(node)) {
        _.forOwn(node, function (cNode, key) {
          walkItem(cNode, key);
        });
      }
    }

    ancestors.pop();
  }
}

function validateOptions (options, obj) {
  var locationParts;
  var shouldDecode;

  if (_.isUndefined(options)) {
    // Default to an empty options object
    options = {};
  } else {
    // Clone the options so we do not alter the ones passed in
    options = _.cloneDeep(options);
  }

  if (!_.isObject(options)) {
    throw new TypeError('options must be an Object');
  } else if (!_.isUndefined(options.resolveCirculars) &&
             !_.isBoolean(options.resolveCirculars)) {
    throw new TypeError('options.resolveCirculars must be a Boolean');
  } else if (!_.isUndefined(options.filter) &&
             !_.isArray(options.filter) &&
             !_.isFunction(options.filter) &&
             !_.isString(options.filter)) {
    throw new TypeError('options.filter must be an Array, a Function of a String');
  } else if (!_.isUndefined(options.includeInvalid) &&
             !_.isBoolean(options.includeInvalid)) {
    throw new TypeError('options.includeInvalid must be a Boolean');
  } else if (!_.isUndefined(options.location) &&
             !_.isString(options.location)) {
    throw new TypeError('options.location must be a String');
  } else if (!_.isUndefined(options.refPreProcessor) &&
             !_.isFunction(options.refPreProcessor)) {
    throw new TypeError('options.refPreProcessor must be a Function');
  } else if (!_.isUndefined(options.refPostProcessor) &&
             !_.isFunction(options.refPostProcessor)) {
    throw new TypeError('options.refPostProcessor must be a Function');
  } else if (!_.isUndefined(options.subDocPath) &&
             !_.isArray(options.subDocPath) &&
             !isPtr(options.subDocPath)) {
    // If a pointer is provided, throw an error if it's not the proper type
    throw new TypeError('options.subDocPath must be an Array of path segments or a valid JSON Pointer');
  }

  // Default to false for allowing circulars
  if (_.isUndefined(options.resolveCirculars)) {
    options.resolveCirculars = false;
  }

  options.filter = makeRefFilter(options);

  // options.location is not officially supported yet but will be when Issue 88 is complete
  if (_.isUndefined(options.location)) {
    options.location = makeAbsolute('./root.json');
  }

  locationParts = options.location.split('#');

  // If options.location contains a fragment, turn it into an options.subDocPath
  if (locationParts.length > 1) {
    options.subDocPath = '#' + locationParts[1];
  }

  shouldDecode = decodeURI(options.location) === options.location;

  // Just to be safe, remove any accidental fragment as it would break things
  options.location = combineURIs(options.location, undefined);

  // If the location was not encoded, meke sure it's not when we get it back (Issue #138)
  if (shouldDecode) {
    options.location = decodeURI(options.location);
  }

  // Set the subDocPath to avoid everyone else having to compute it
  options.subDocPath = makeSubDocPath(options);

  if (!_.isUndefined(obj)) {
    try {
      findValue(obj, options.subDocPath);
    } catch (err) {
      err.message = err.message.replace('JSON Pointer', 'options.subDocPath');

      throw err;
    }
  }

  return options;
}

function decodePath (path) {
  if (!_.isArray(path)) {
    throw new TypeError('path must be an array');
  }

  return path.map(function (seg) {
    if (!_.isString(seg)) {
      seg = JSON.stringify(seg);
    }

    return seg.replace(/~1/g, '/').replace(/~0/g, '~');
  });
}

function encodePath (path) {
  if (!_.isArray(path)) {
    throw new TypeError('path must be an array');
  }

  return path.map(function (seg) {
    if (!_.isString(seg)) {
      seg = JSON.stringify(seg);
    }

    return seg.replace(/~/g, '~0').replace(/\//g, '~1');
  });
}

function findRefs (obj, options) {
  var refs = {};

  // Validate the provided document
  if (!_.isArray(obj) && !_.isObject(obj)) {
    throw new TypeError('obj must be an Array or an Object');
  }

  // Validate options
  options = validateOptions(options, obj);

  // Walk the document (or sub document) and find all JSON References
  walk(findAncestors(obj, options.subDocPath),
       findValue(obj, options.subDocPath),
       _.cloneDeep(options.subDocPath),
       function (ancestors, node, path) {
         var processChildren = true;
         var refDetails;
         var refPtr;

         if (isRefLike(node)) {
           // Pre-process the node when necessary
           if (!_.isUndefined(options.refPreProcessor)) {
             node = options.refPreProcessor(_.cloneDeep(node), path);
           }

           refDetails = getRefDetails(node);

           // Post-process the reference details
           if (!_.isUndefined(options.refPostProcessor)) {
             refDetails = options.refPostProcessor(refDetails, path);
           }

           if (options.filter(refDetails, path)) {
             refPtr = pathToPtr(path);

             refs[refPtr] = refDetails;
           }

           // Whenever a JSON Reference has extra children, its children should not be processed.
           //   See: http://tools.ietf.org/html/draft-pbryan-zyp-json-ref-03#section-3
           if (getExtraRefKeys(node).length > 0) {
             processChildren = false;
           }
         }

         return processChildren;
       });

  return refs;
}

function findRefsAt (location, options) {
  var allTasks = Promise.resolve();

  allTasks = allTasks
    .then(function () {
      // Validate the provided location
      if (!_.isString(location)) {
        throw new TypeError('location must be a string');
      }

      if (_.isUndefined(options)) {
        options = {};
      }

      if (_.isObject(options)) {
        // Add the location to the options for processing/validation
        options.location = location;
      }

      // Validate options
      options = validateOptions(options);

      return getRemoteDocument(options.location, options);
    })
    .then(function (res) {
      var cacheEntry = _.cloneDeep(remoteCache[options.location]);
      var cOptions = _.cloneDeep(options);

      if (_.isUndefined(cacheEntry.refs)) {
        // Do not filter any references so the cache is complete
        delete cOptions.filter;
        delete cOptions.subDocPath;

        cOptions.includeInvalid = true;

        remoteCache[options.location].refs = findRefs(res, cOptions);
      }

      // Add the filter options back
      if (!_.isUndefined(options.filter)) {
        cOptions.filter = options.filter;
      }

      // This will use the cache so don't worry about calling it twice
      return {
        refs: findRefs(res, cOptions),
        value: res
      };
    });

  return allTasks;
}

function getRefDetails (obj) {
  var details = {
    def: obj
  };
  var cacheKey;
  var extraKeys;
  var uriDetails;

  try {
    // This will throw so the result doesn't matter
    isRefLike(obj, true);

    cacheKey = obj.$ref;
    uriDetails = uriDetailsCache[cacheKey];

    if (_.isUndefined(uriDetails)) {
      uriDetails = uriDetailsCache[cacheKey] = parseURI(cacheKey);
    }

    details.uri = cacheKey;
    details.uriDetails = uriDetails;

    if (_.isUndefined(uriDetails.error)) {
      details.type = getRefType(details);

      // Validate the JSON Pointer
      try {
        if (['#', '/'].indexOf(cacheKey[0]) > -1) {
          isPtr(cacheKey, true);
        } else if (cacheKey.indexOf('#') > -1) {
          isPtr(uriDetails.fragment, true);
        }
      } catch (err) {
        details.error = err.message;
        details.type = 'invalid';
      }
    } else {
      details.error = details.uriDetails.error;
      details.type = 'invalid';
    }

    // Identify warning
    extraKeys = getExtraRefKeys(obj);

    if (extraKeys.length > 0) {
      details.warning = 'Extra JSON Reference properties will be ignored: ' + extraKeys.join(', ');
    }
  } catch (err) {
    details.error = err.message;
    details.type = 'invalid';
  }

  return details;
}

function isPtr (ptr, throwWithDetails) {
  var valid = true;
  var firstChar;

  try {
    if (_.isString(ptr)) {
      if (ptr !== '') {
        firstChar = ptr.charAt(0);

        if (['#', '/'].indexOf(firstChar) === -1) {
          throw new Error('ptr must start with a / or #/');
        } else if (firstChar === '#' && ptr !== '#' && ptr.charAt(1) !== '/') {
          throw new Error('ptr must start with a / or #/');
        } else if (ptr.match(badPtrTokenRegex)) {
          throw new Error('ptr has invalid token(s)');
        }
      }
    } else {
      throw new Error('ptr is not a String');
    }
  } catch (err) {
    if (throwWithDetails === true) {
      throw err;
    }

    valid = false;
  }

  return valid;
}

function isRef (obj, throwWithDetails) {
  return isRefLike(obj, throwWithDetails) && getRefDetails(obj).type !== 'invalid';
}

function pathFromPtr (ptr) {
  try {
    isPtr(ptr, true);
  } catch (err) {
    throw new Error('ptr must be a JSON Pointer: ' + err.message);
  }

  var segments = ptr.split('/');

  // Remove the first segment
  segments.shift();

  return decodePath(segments);
}

function pathToPtr (path, hashPrefix) {
  if (!_.isArray(path)) {
    throw new Error('path must be an Array');
  }

  // Encode each segment and return
  return (hashPrefix !== false ? '#' : '') + (path.length > 0 ? '/' : '') + encodePath(path).join('/');
}

function resolveRefs (obj, options) {
  var allTasks = Promise.resolve();

  allTasks = allTasks
    .then(function () {
      // Validate the provided document
      if (!_.isArray(obj) && !_.isObject(obj)) {
        throw new TypeError('obj must be an Array or an Object');
      }

      // Validate options
      options = validateOptions(options, obj);

      // Clone the input so we do not alter it
      obj = _.cloneDeep(obj);
    })
    .then(function () {
      var metadata = {
        deps: {}, // To avoid processing the same refernece twice, and for circular reference identification
        docs: {}, // Cache to avoid processing the same document more than once
        refs: {} // Reference locations and their metadata
      };

      return buildRefModel(obj, options, metadata)
        .then(function () {
          return metadata;
        });
    })
    .then(function (results) {
      var allRefs = {};
      var circularPaths = [];
      var circulars = [];
      var depGraph = new gl.Graph();
      var fullLocation = makeAbsolute(options.location);
      var refsRoot = fullLocation + pathToPtr(options.subDocPath);
      var relativeBase = path.dirname(fullLocation);

      // Identify circulars

      // Add nodes first
      Object.keys(results.deps).forEach(function (node) {
        depGraph.setNode(node);
      });

      // Add edges
      _.forOwn(results.deps, function (props, node) {
        _.forOwn(props, function (dep) {
          depGraph.setEdge(node, dep);
        });
      });

      circularPaths = gl.alg.findCycles(depGraph);

      // Create a unique list of circulars
      circularPaths.forEach(function (path) {
        path.forEach(function (seg) {
          if (circulars.indexOf(seg) === -1) {
            circulars.push(seg);
          }
        });
      });

      // Identify circulars
      _.forOwn(results.deps, function (props, node) {
        _.forOwn(props, function (dep, prop) {
          var isCircular = false;
          var refPtr = node + prop.slice(1);
          var refDetails = results.refs[node + prop.slice(1)];
          var remote = isRemote(refDetails);
          var pathIndex;

          if (circulars.indexOf(dep) > -1) {
            // Figure out if the circular is part of a circular chain or just a reference to a circular
            circularPaths.forEach(function (path) {
              // Short circuit
              if (isCircular) {
                return;
              }

              pathIndex = path.indexOf(dep);

              if (pathIndex > -1) {
                // Check each path segment to see if the reference location is beneath one of its segments
                path.forEach(function (seg) {
                  // Short circuit
                  if (isCircular) {
                    return;
                  }

                  if (refPtr.indexOf(seg + '/') === 0) {
                    // If the reference is local, mark it as circular but if it's a remote reference, only mark it
                    // circular if the matching path is the last path segment or its match is not to a document root
                    if (!remote || pathIndex === path.length - 1 || dep[dep.length - 1] !== '#') {
                      isCircular = true;
                    }
                  }
                });
              }
            });
          }

          if (isCircular) {
            // Update all references and reference details
            refDetails.circular = true;
          }
        });
      });

      // Resolve the references in reverse order since the current order is top-down
      _.forOwn(Object.keys(results.deps).reverse(), function (parentPtr) {
        var deps = results.deps[parentPtr];
        var pPtrParts = parentPtr.split('#');
        var pDocument = results.docs[pPtrParts[0]];
        var pPtrPath = pathFromPtr(pPtrParts[1]);

        _.forOwn(deps, function (dep, prop) {
          var depParts = dep.split('#');
          var dDocument = results.docs[depParts[0]];
          var dPtrPath = pPtrPath.concat(pathFromPtr(prop));
          var refDetails = results.refs[pPtrParts[0] + pathToPtr(dPtrPath)];

          // Resolve reference if valid
          if (_.isUndefined(refDetails.error) && _.isUndefined(refDetails.missing)) {
            if (!options.resolveCirculars && refDetails.circular) {
              refDetails.value = _.cloneDeep(refDetails.def);
            } else {
              try {
                refDetails.value = findValue(dDocument, pathFromPtr(depParts[1]));
              } catch (err) {
                markMissing(refDetails, err);

                return;
              }

              // If the reference is at the root of the document, replace the document in the cache.  Otherwise, replace
              // the value in the appropriate location in the document cache.
              if (pPtrParts[1] === '' && prop === '#') {
                results.docs[pPtrParts[0]] = refDetails.value;
              } else {
                setValue(pDocument, dPtrPath, refDetails.value);
              }
            }
          }
        });
      });

      function walkRefs (root, refPtr, refPath) {
        var refPtrParts = refPtr.split('#');
        var refDetails = results.refs[refPtr];
        var refDeps;

        // Record the reference (relative to the root document unless the reference is in the root document)
        allRefs[refPtrParts[0] === options.location ?
                  '#' + refPtrParts[1] :
                  pathToPtr(options.subDocPath.concat(refPath))] = refDetails;

        // Do not walk invalid references
        if (refDetails.circular || !isValid(refDetails)) {
          // Sanitize errors
          if (!refDetails.circular && refDetails.error) {
            // The way we use findRefs now results in an error that doesn't match the expectation
            refDetails.error = refDetails.error.replace('options.subDocPath', 'JSON Pointer');

            // Update the error to use the appropriate JSON Pointer
            if (refDetails.error.indexOf('#') > -1) {
              refDetails.error = refDetails.error.replace(refDetails.uri.substr(refDetails.uri.indexOf('#')),
                                                          refDetails.uri);
            }

            // Report errors opening files as JSON Pointer errors
            if (refDetails.error.indexOf('ENOENT:') === 0 || refDetails.error.indexOf('Not Found') === 0) {
              refDetails.error = 'JSON Pointer points to missing location: ' + refDetails.uri;
            }
          }

          return;
        }

        refDeps = results.deps[refDetails.refdId];

        if (refDetails.refdId.indexOf(root) !== 0) {
          Object.keys(refDeps).forEach(function (prop) {
            walkRefs(refDetails.refdId, refDetails.refdId + prop.substr(1), refPath.concat(pathFromPtr(prop)));
          });
        }
      }

      // For performance reasons, we only process a document (or sub document) and each reference once ever.  This means
      // that if we want to provide the full picture as to what paths in the resolved document were created as a result
      // of a reference, we have to take our fully-qualified reference locations and expand them to be all local based
      // on the original document.
      Object.keys(results.refs).forEach(function (refPtr) {
        var refDetails = results.refs[refPtr];
        var fqURISegments;
        var uriSegments;

        // Make all fully-qualified reference URIs relative to the document root (if necessary).  This step is done here
        // for performance reasons instead of below when the official sanitization process runs.
        if (refDetails.type !== 'invalid') {
          // Remove the trailing hash from document root references if they weren't in the original URI
          if (refDetails.fqURI[refDetails.fqURI.length - 1] === '#' &&
                refDetails.uri[refDetails.uri.length - 1] !== '#') {
            refDetails.fqURI = refDetails.fqURI.substr(0, refDetails.fqURI.length - 1);
          }

          fqURISegments = refDetails.fqURI.split('/');
          uriSegments = refDetails.uri.split('/');

          // The fully-qualified URI is unencoded so to keep the original formatting of the URI (encoded vs. unencoded),
          // we need to replace each URI segment in reverse order.
          _.times(uriSegments.length - 1, function (time) {
            var nSeg = uriSegments[uriSegments.length - time - 1];
            var pSeg = uriSegments[uriSegments.length - time];
            var fqSegIndex = fqURISegments.length - time - 1;

            if (nSeg === '.' || nSeg === '..' || pSeg === '..') {
              return;
            }

            fqURISegments[fqSegIndex] = nSeg;
          });

          refDetails.fqURI = fqURISegments.join('/');

          // Make the fully-qualified URIs relative to the document root
          if (refDetails.fqURI.indexOf(fullLocation) === 0) {
            refDetails.fqURI = refDetails.fqURI.replace(fullLocation, '');
          } else if (refDetails.fqURI.indexOf(relativeBase) === 0) {
            refDetails.fqURI = refDetails.fqURI.replace(relativeBase, '');
          }

          if (refDetails.fqURI[0] === '/') {
            refDetails.fqURI = '.' + refDetails.fqURI;
          }
        }

        // We only want to process references found at or beneath the provided document and sub-document path
        if (refPtr.indexOf(refsRoot) !== 0) {
          return;
        }

        walkRefs(refsRoot, refPtr, pathFromPtr(refPtr.substr(refsRoot.length)));
      });

      // Sanitize the reference details
      _.forOwn(allRefs, function (refDetails, refPtr) {
        // Delete the reference id used for dependency tracking and circular identification
        delete refDetails.refdId;

        // For locally-circular references, update the $ref to be fully qualified (Issue #175)
        if (refDetails.circular && refDetails.type === 'local') {
          refDetails.value.$ref = refDetails.fqURI;

          setValue(results.docs[fullLocation], pathFromPtr(refPtr), refDetails.value);
        }

        // To avoid the error message being URI encoded/decoded by mistake, replace the current JSON Pointer with the
        // value in the JSON Reference definition.
        if (refDetails.missing) {
          refDetails.error = refDetails.error.split(': ')[0] + ': ' + refDetails.def.$ref;
        }
      });

      return {
        refs: allRefs,
        resolved: results.docs[fullLocation]
      };
    });

  return allTasks;
}

function resolveRefsAt (location, options) {
  var allTasks = Promise.resolve();

  allTasks = allTasks
    .then(function () {
      // Validate the provided location
      if (!_.isString(location)) {
        throw new TypeError('location must be a string');
      }

      if (_.isUndefined(options)) {
        options = {};
      }

      if (_.isObject(options)) {
        // Add the location to the options for processing/validation
        options.location = location;
      }

      // Validate options
      options = validateOptions(options);

      return getRemoteDocument(options.location, options);
    })
    .then(function (res) {
      return resolveRefs(res, options)
        .then(function (res2) {
          return {
            refs: res2.refs,
            resolved: res2.resolved,
            value: res
          };
        });
    });

  return allTasks;
}

/**
 * Various utilities for JSON References *(http://tools.ietf.org/html/draft-pbryan-zyp-json-ref-03)* and
 * JSON Pointers *(https://tools.ietf.org/html/rfc6901)*.
 *
 * @module json-refs
 */

/**
 * A number of functions exported below are used within the exported functions.  Typically, I would use a function
 * declaration _(with documenation)_ above and then just export a reference to the function but due to a bug in JSDoc
 * (https://github.com/jsdoc3/jsdoc/issues/679), this breaks the generated API documentation and TypeScript
 * declarations.  So that's why each `module.exports` below basically just wraps a call to the function declaration.
 */

 /**
 * Clears the internal cache of remote documents, reference details, etc.
 */
module.exports.clearCache = function () {
  remoteCache = {};
};

/**
 * Takes an array of path segments and decodes the JSON Pointer tokens in them.
 *
 * @param {string[]} path - The array of path segments
 *
 * @returns {string[]} the array of path segments with their JSON Pointer tokens decoded
 *
 * @throws {Error} if the path is not an `Array`
 *
 * @see {@link https://tools.ietf.org/html/rfc6901#section-3}
 */
module.exports.decodePath = function (path) {
  return decodePath(path);
};

/**
 * Takes an array of path segments and encodes the special JSON Pointer characters in them.
 *
 * @param {string[]} path - The array of path segments
 *
 * @returns {string[]} the array of path segments with their JSON Pointer tokens encoded
 *
 * @throws {Error} if the path is not an `Array`
 *
 * @see {@link https://tools.ietf.org/html/rfc6901#section-3}
 */
module.exports.encodePath = function (path) {
  return encodePath(path);
};

/**
 * Finds JSON References defined within the provided array/object.
 *
 * @param {array|object} obj - The structure to find JSON References within
 * @param {module:json-refs.JsonRefsOptions} [options] - The JsonRefs options
 *
 * @returns {Object.<string, module:json-refs.UnresolvedRefDetails|undefined>} an object whose keys are JSON Pointers
 * *(fragment version)* to where the JSON Reference is defined and whose values are {@link UnresolvedRefDetails}.
 *
 * @throws {Error} when the input arguments fail validation or if `options.subDocPath` points to an invalid location
 *
 * @example
 * // Finding all valid references
 * var allRefs = JsonRefs.findRefs(obj);
 * // Finding all remote references
 * var remoteRefs = JsonRefs.findRefs(obj, {filter: ['relative', 'remote']});
 * // Finding all invalid references
 * var invalidRefs = JsonRefs.findRefs(obj, {filter: 'invalid', includeInvalid: true});
 */
module.exports.findRefs = function (obj, options) {
  return findRefs(obj, options);
};

/**
 * Finds JSON References defined within the document at the provided location.
 *
 * This API is identical to {@link findRefs} except this API will retrieve a remote document and then
 * return the result of {@link findRefs} on the retrieved document.
 *
 * @param {string} location - The location to retrieve *(Can be relative or absolute, just make sure you look at the
 * {@link module:json-refs.JsonRefsOptions|options documentation} to see how relative references are handled.)*
 * @param {module:json-refs.JsonRefsOptions} [options] - The JsonRefs options
 *
 * @returns {Promise<module:json-refs.RetrievedRefsResults>} a promise that resolves a
 * {@link module:json-refs.RetrievedRefsResults} and rejects with an `Error` when the input arguments fail validation,
 * when `options.subDocPath` points to an invalid location or when the location argument points to an unloadable
 * resource
 *
 * @example
 * // Example that only resolves references within a sub document
 * JsonRefs.findRefsAt('http://petstore.swagger.io/v2/swagger.json', {
 *     subDocPath: '#/definitions'
 *   })
 *   .then(function (res) {
 *      // Do something with the response
 *      //
 *      // res.refs: JSON Reference locations and details
 *      // res.value: The retrieved document
 *   }, function (err) {
 *     console.log(err.stack);
 *   });
 */
module.exports.findRefsAt = function (location, options) {
  return findRefsAt(location, options);
};

/**
 * Returns detailed information about the JSON Reference.
 *
 * @param {object} obj - The JSON Reference definition
 *
 * @returns {module:json-refs.UnresolvedRefDetails} the detailed information
 */
module.exports.getRefDetails = function (obj) {
  return getRefDetails(obj);
};

/**
 * Returns whether the argument represents a JSON Pointer.
 *
 * A string is a JSON Pointer if the following are all true:
 *
 *   * The string is of type `String`
 *   * The string must be empty, `#` or start with a `/` or `#/`
 *
 * @param {string} ptr - The string to check
 * @param {boolean} [throwWithDetails=false] - Whether or not to throw an `Error` with the details as to why the value
 * provided is invalid
 *
 * @returns {boolean} the result of the check
 *
 * @throws {error} when the provided value is invalid and the `throwWithDetails` argument is `true`
 *
 * @see {@link https://tools.ietf.org/html/rfc6901#section-3}
 *
 * @example
 * // Separating the different ways to invoke isPtr for demonstration purposes
 * if (isPtr(str)) {
 *   // Handle a valid JSON Pointer
 * } else {
 *   // Get the reason as to why the value is not a JSON Pointer so you can fix/report it
 *   try {
 *     isPtr(str, true);
 *   } catch (err) {
 *     // The error message contains the details as to why the provided value is not a JSON Pointer
 *   }
 * }
 */
module.exports.isPtr = function (ptr, throwWithDetails) {
  return isPtr(ptr, throwWithDetails);
};

/**
 * Returns whether the argument represents a JSON Reference.
 *
 * An object is a JSON Reference only if the following are all true:
 *
 *   * The object is of type `Object`
 *   * The object has a `$ref` property
 *   * The `$ref` property is a valid URI *(We do not require 100% strict URIs and will handle unescaped special
 *     characters.)*
 *
 * @param {object} obj - The object to check
 * @param {boolean} [throwWithDetails=false] - Whether or not to throw an `Error` with the details as to why the value
 * provided is invalid
 *
 * @returns {boolean} the result of the check
 *
 * @throws {error} when the provided value is invalid and the `throwWithDetails` argument is `true`
 *
 * @see {@link http://tools.ietf.org/html/draft-pbryan-zyp-json-ref-03#section-3}
 *
 * @example
 * // Separating the different ways to invoke isRef for demonstration purposes
 * if (isRef(obj)) {
 *   // Handle a valid JSON Reference
 * } else {
 *   // Get the reason as to why the value is not a JSON Reference so you can fix/report it
 *   try {
 *     isRef(str, true);
 *   } catch (err) {
 *     // The error message contains the details as to why the provided value is not a JSON Reference
 *   }
 * }
 */
module.exports.isRef = function (obj, throwWithDetails) {
  return isRef(obj, throwWithDetails);
};

/**
 * Returns an array of path segments for the provided JSON Pointer.
 *
 * @param {string} ptr - The JSON Pointer
 *
 * @returns {string[]} the path segments
 *
 * @throws {Error} if the provided `ptr` argument is not a JSON Pointer
 */
module.exports.pathFromPtr = function (ptr) {
  return pathFromPtr(ptr);
};

/**
 * Returns a JSON Pointer for the provided array of path segments.
 *
 * **Note:** If a path segment in `path` is not a `String`, it will be converted to one using `JSON.stringify`.
 *
 * @param {string[]} path - The array of path segments
 * @param {boolean} [hashPrefix=true] - Whether or not create a hash-prefixed JSON Pointer
 *
 * @returns {string} the corresponding JSON Pointer
 *
 * @throws {Error} if the `path` argument is not an array
 */
module.exports.pathToPtr = function (path, hashPrefix) {
  return pathToPtr(path, hashPrefix);
};

/**
 * Finds JSON References defined within the provided array/object and resolves them.
 *
 * @param {array|object} obj - The structure to find JSON References within
 * @param {module:json-refs.JsonRefsOptions} [options] - The JsonRefs options
 *
 * @returns {Promise<module:json-refs.ResolvedRefsResults>} a promise that resolves a
 * {@link module:json-refs.ResolvedRefsResults} and rejects with an `Error` when the input arguments fail validation,
 * when `options.subDocPath` points to an invalid location or when the location argument points to an unloadable
 * resource
 *
 * @example
 * // Example that only resolves relative and remote references
 * JsonRefs.resolveRefs(swaggerObj, {
 *     filter: ['relative', 'remote']
 *   })
 *   .then(function (res) {
 *      // Do something with the response
 *      //
 *      // res.refs: JSON Reference locations and details
 *      // res.resolved: The document with the appropriate JSON References resolved
 *   }, function (err) {
 *     console.log(err.stack);
 *   });
 */
module.exports.resolveRefs = function (obj, options) {
  return resolveRefs(obj, options);
};

/**
 * Resolves JSON References defined within the document at the provided location.
 *
 * This API is identical to {@link module:json-refs.resolveRefs} except this API will retrieve a remote document and
 * then return the result of {@link module:json-refs.resolveRefs} on the retrieved document.
 *
 * @param {string} location - The location to retrieve *(Can be relative or absolute, just make sure you look at the
 * {@link module:json-refs.JsonRefsOptions|options documentation} to see how relative references are handled.)*
 * @param {module:json-refs.JsonRefsOptions} [options] - The JsonRefs options
 *
 * @returns {Promise<module:json-refs.RetrievedResolvedRefsResults>} a promise that resolves a
 * {@link module:json-refs.RetrievedResolvedRefsResults} and rejects with an `Error` when the input arguments fail
 * validation, when `options.subDocPath` points to an invalid location or when the location argument points to an
 * unloadable resource
 *
 * @example
 * // Example that loads a JSON document (No options.loaderOptions.processContent required) and resolves all references
 * JsonRefs.resolveRefsAt('./swagger.json')
 *   .then(function (res) {
 *      // Do something with the response
 *      //
 *      // res.refs: JSON Reference locations and details
 *      // res.resolved: The document with the appropriate JSON References resolved
 *      // res.value: The retrieved document
 *   }, function (err) {
 *     console.log(err.stack);
 *   });
 */
module.exports.resolveRefsAt = function (location, options) {
  return resolveRefsAt(location, options);
};
