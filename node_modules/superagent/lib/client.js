"use strict";

function _typeof(obj) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (obj) { return typeof obj; } : function (obj) { return obj && "function" == typeof Symbol && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; }, _typeof(obj); }

function _createForOfIteratorHelper(o, allowArrayLike) { var it = typeof Symbol !== "undefined" && o[Symbol.iterator] || o["@@iterator"]; if (!it) { if (Array.isArray(o) || (it = _unsupportedIterableToArray(o)) || allowArrayLike && o && typeof o.length === "number") { if (it) o = it; var i = 0; var F = function F() {}; return { s: F, n: function n() { if (i >= o.length) return { done: true }; return { done: false, value: o[i++] }; }, e: function e(_e) { throw _e; }, f: F }; } throw new TypeError("Invalid attempt to iterate non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); } var normalCompletion = true, didErr = false, err; return { s: function s() { it = it.call(o); }, n: function n() { var step = it.next(); normalCompletion = step.done; return step; }, e: function e(_e2) { didErr = true; err = _e2; }, f: function f() { try { if (!normalCompletion && it.return != null) it.return(); } finally { if (didErr) throw err; } } }; }

function _unsupportedIterableToArray(o, minLen) { if (!o) return; if (typeof o === "string") return _arrayLikeToArray(o, minLen); var n = Object.prototype.toString.call(o).slice(8, -1); if (n === "Object" && o.constructor) n = o.constructor.name; if (n === "Map" || n === "Set") return Array.from(o); if (n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)) return _arrayLikeToArray(o, minLen); }

function _arrayLikeToArray(arr, len) { if (len == null || len > arr.length) len = arr.length; for (var i = 0, arr2 = new Array(len); i < len; i++) { arr2[i] = arr[i]; } return arr2; }

/**
 * Root reference for iframes.
 */
var root;

if (typeof window !== 'undefined') {
  // Browser window
  root = window;
} else if (typeof self === 'undefined') {
  // Other environments
  console.warn('Using browser-only version of superagent in non-browser environment');
  root = void 0;
} else {
  // Web Worker
  root = self;
}

var Emitter = require('component-emitter');

var safeStringify = require('fast-safe-stringify');

var qs = require('qs');

var RequestBase = require('./request-base');

var _require = require('./utils'),
    isObject = _require.isObject,
    mixin = _require.mixin,
    hasOwn = _require.hasOwn;

var ResponseBase = require('./response-base');

var Agent = require('./agent-base');
/**
 * Noop.
 */


function noop() {}
/**
 * Expose `request`.
 */


module.exports = function (method, url) {
  // callback
  if (typeof url === 'function') {
    return new exports.Request('GET', method).end(url);
  } // url first


  if (arguments.length === 1) {
    return new exports.Request('GET', method);
  }

  return new exports.Request(method, url);
};

exports = module.exports;
var request = exports;
exports.Request = Request;
/**
 * Determine XHR.
 */

request.getXHR = function () {
  if (root.XMLHttpRequest && (!root.location || root.location.protocol !== 'file:')) {
    return new XMLHttpRequest();
  }

  throw new Error('Browser-only version of superagent could not find XHR');
};
/**
 * Removes leading and trailing whitespace, added to support IE.
 *
 * @param {String} s
 * @return {String}
 * @api private
 */


var trim = ''.trim ? function (s) {
  return s.trim();
} : function (s) {
  return s.replace(/(^\s*|\s*$)/g, '');
};
/**
 * Serialize the given `obj`.
 *
 * @param {Object} obj
 * @return {String}
 * @api private
 */

function serialize(object) {
  if (!isObject(object)) return object;
  var pairs = [];

  for (var key in object) {
    if (hasOwn(object, key)) pushEncodedKeyValuePair(pairs, key, object[key]);
  }

  return pairs.join('&');
}
/**
 * Helps 'serialize' with serializing arrays.
 * Mutates the pairs array.
 *
 * @param {Array} pairs
 * @param {String} key
 * @param {Mixed} val
 */


function pushEncodedKeyValuePair(pairs, key, value) {
  if (value === undefined) return;

  if (value === null) {
    pairs.push(encodeURI(key));
    return;
  }

  if (Array.isArray(value)) {
    var _iterator = _createForOfIteratorHelper(value),
        _step;

    try {
      for (_iterator.s(); !(_step = _iterator.n()).done;) {
        var v = _step.value;
        pushEncodedKeyValuePair(pairs, key, v);
      }
    } catch (err) {
      _iterator.e(err);
    } finally {
      _iterator.f();
    }
  } else if (isObject(value)) {
    for (var subkey in value) {
      if (hasOwn(value, subkey)) pushEncodedKeyValuePair(pairs, "".concat(key, "[").concat(subkey, "]"), value[subkey]);
    }
  } else {
    pairs.push(encodeURI(key) + '=' + encodeURIComponent(value));
  }
}
/**
 * Expose serialization method.
 */


request.serializeObject = serialize;
/**
 * Parse the given x-www-form-urlencoded `str`.
 *
 * @param {String} str
 * @return {Object}
 * @api private
 */

function parseString(string_) {
  var object = {};
  var pairs = string_.split('&');
  var pair;
  var pos;

  for (var i = 0, length_ = pairs.length; i < length_; ++i) {
    pair = pairs[i];
    pos = pair.indexOf('=');

    if (pos === -1) {
      object[decodeURIComponent(pair)] = '';
    } else {
      object[decodeURIComponent(pair.slice(0, pos))] = decodeURIComponent(pair.slice(pos + 1));
    }
  }

  return object;
}
/**
 * Expose parser.
 */


request.parseString = parseString;
/**
 * Default MIME type map.
 *
 *     superagent.types.xml = 'application/xml';
 *
 */

request.types = {
  html: 'text/html',
  json: 'application/json',
  xml: 'text/xml',
  urlencoded: 'application/x-www-form-urlencoded',
  form: 'application/x-www-form-urlencoded',
  'form-data': 'application/x-www-form-urlencoded'
};
/**
 * Default serialization map.
 *
 *     superagent.serialize['application/xml'] = function(obj){
 *       return 'generated xml here';
 *     };
 *
 */

request.serialize = {
  'application/x-www-form-urlencoded': qs.stringify,
  'application/json': safeStringify
};
/**
 * Default parsers.
 *
 *     superagent.parse['application/xml'] = function(str){
 *       return { object parsed from str };
 *     };
 *
 */

request.parse = {
  'application/x-www-form-urlencoded': parseString,
  'application/json': JSON.parse
};
/**
 * Parse the given header `str` into
 * an object containing the mapped fields.
 *
 * @param {String} str
 * @return {Object}
 * @api private
 */

function parseHeader(string_) {
  var lines = string_.split(/\r?\n/);
  var fields = {};
  var index;
  var line;
  var field;
  var value;

  for (var i = 0, length_ = lines.length; i < length_; ++i) {
    line = lines[i];
    index = line.indexOf(':');

    if (index === -1) {
      // could be empty line, just skip it
      continue;
    }

    field = line.slice(0, index).toLowerCase();
    value = trim(line.slice(index + 1));
    fields[field] = value;
  }

  return fields;
}
/**
 * Check if `mime` is json or has +json structured syntax suffix.
 *
 * @param {String} mime
 * @return {Boolean}
 * @api private
 */


function isJSON(mime) {
  // should match /json or +json
  // but not /json-seq
  return /[/+]json($|[^-\w])/i.test(mime);
}
/**
 * Initialize a new `Response` with the given `xhr`.
 *
 *  - set flags (.ok, .error, etc)
 *  - parse header
 *
 * Examples:
 *
 *  Aliasing `superagent` as `request` is nice:
 *
 *      request = superagent;
 *
 *  We can use the promise-like API, or pass callbacks:
 *
 *      request.get('/').end(function(res){});
 *      request.get('/', function(res){});
 *
 *  Sending data can be chained:
 *
 *      request
 *        .post('/user')
 *        .send({ name: 'tj' })
 *        .end(function(res){});
 *
 *  Or passed to `.send()`:
 *
 *      request
 *        .post('/user')
 *        .send({ name: 'tj' }, function(res){});
 *
 *  Or passed to `.post()`:
 *
 *      request
 *        .post('/user', { name: 'tj' })
 *        .end(function(res){});
 *
 * Or further reduced to a single call for simple cases:
 *
 *      request
 *        .post('/user', { name: 'tj' }, function(res){});
 *
 * @param {XMLHTTPRequest} xhr
 * @param {Object} options
 * @api private
 */


function Response(request_) {
  this.req = request_;
  this.xhr = this.req.xhr; // responseText is accessible only if responseType is '' or 'text' and on older browsers

  this.text = this.req.method !== 'HEAD' && (this.xhr.responseType === '' || this.xhr.responseType === 'text') || typeof this.xhr.responseType === 'undefined' ? this.xhr.responseText : null;
  this.statusText = this.req.xhr.statusText;
  var status = this.xhr.status; // handle IE9 bug: http://stackoverflow.com/questions/10046972/msie-returns-status-code-of-1223-for-ajax-request

  if (status === 1223) {
    status = 204;
  }

  this._setStatusProperties(status);

  this.headers = parseHeader(this.xhr.getAllResponseHeaders());
  this.header = this.headers; // getAllResponseHeaders sometimes falsely returns "" for CORS requests, but
  // getResponseHeader still works. so we get content-type even if getting
  // other headers fails.

  this.header['content-type'] = this.xhr.getResponseHeader('content-type');

  this._setHeaderProperties(this.header);

  if (this.text === null && request_._responseType) {
    this.body = this.xhr.response;
  } else {
    this.body = this.req.method === 'HEAD' ? null : this._parseBody(this.text ? this.text : this.xhr.response);
  }
}

mixin(Response.prototype, ResponseBase.prototype);
/**
 * Parse the given body `str`.
 *
 * Used for auto-parsing of bodies. Parsers
 * are defined on the `superagent.parse` object.
 *
 * @param {String} str
 * @return {Mixed}
 * @api private
 */

Response.prototype._parseBody = function (string_) {
  var parse = request.parse[this.type];

  if (this.req._parser) {
    return this.req._parser(this, string_);
  }

  if (!parse && isJSON(this.type)) {
    parse = request.parse['application/json'];
  }

  return parse && string_ && (string_.length > 0 || string_ instanceof Object) ? parse(string_) : null;
};
/**
 * Return an `Error` representative of this response.
 *
 * @return {Error}
 * @api public
 */


Response.prototype.toError = function () {
  var req = this.req;
  var method = req.method;
  var url = req.url;
  var message = "cannot ".concat(method, " ").concat(url, " (").concat(this.status, ")");
  var error = new Error(message);
  error.status = this.status;
  error.method = method;
  error.url = url;
  return error;
};
/**
 * Expose `Response`.
 */


request.Response = Response;
/**
 * Initialize a new `Request` with the given `method` and `url`.
 *
 * @param {String} method
 * @param {String} url
 * @api public
 */

function Request(method, url) {
  var self = this;
  this._query = this._query || [];
  this.method = method;
  this.url = url;
  this.header = {}; // preserves header name case

  this._header = {}; // coerces header names to lowercase

  this.on('end', function () {
    var error = null;
    var res = null;

    try {
      res = new Response(self);
    } catch (err) {
      error = new Error('Parser is unable to parse the response');
      error.parse = true;
      error.original = err; // issue #675: return the raw response if the response parsing fails

      if (self.xhr) {
        // ie9 doesn't have 'response' property
        error.rawResponse = typeof self.xhr.responseType === 'undefined' ? self.xhr.responseText : self.xhr.response; // issue #876: return the http status code if the response parsing fails

        error.status = self.xhr.status ? self.xhr.status : null;
        error.statusCode = error.status; // backwards-compat only
      } else {
        error.rawResponse = null;
        error.status = null;
      }

      return self.callback(error);
    }

    self.emit('response', res);
    var new_error;

    try {
      if (!self._isResponseOK(res)) {
        new_error = new Error(res.statusText || res.text || 'Unsuccessful HTTP response');
      }
    } catch (err) {
      new_error = err; // ok() callback can throw
    } // #1000 don't catch errors from the callback to avoid double calling it


    if (new_error) {
      new_error.original = error;
      new_error.response = res;
      new_error.status = new_error.status || res.status;
      self.callback(new_error, res);
    } else {
      self.callback(null, res);
    }
  });
}
/**
 * Mixin `Emitter` and `RequestBase`.
 */
// eslint-disable-next-line new-cap


Emitter(Request.prototype);
mixin(Request.prototype, RequestBase.prototype);
/**
 * Set Content-Type to `type`, mapping values from `request.types`.
 *
 * Examples:
 *
 *      superagent.types.xml = 'application/xml';
 *
 *      request.post('/')
 *        .type('xml')
 *        .send(xmlstring)
 *        .end(callback);
 *
 *      request.post('/')
 *        .type('application/xml')
 *        .send(xmlstring)
 *        .end(callback);
 *
 * @param {String} type
 * @return {Request} for chaining
 * @api public
 */

Request.prototype.type = function (type) {
  this.set('Content-Type', request.types[type] || type);
  return this;
};
/**
 * Set Accept to `type`, mapping values from `request.types`.
 *
 * Examples:
 *
 *      superagent.types.json = 'application/json';
 *
 *      request.get('/agent')
 *        .accept('json')
 *        .end(callback);
 *
 *      request.get('/agent')
 *        .accept('application/json')
 *        .end(callback);
 *
 * @param {String} accept
 * @return {Request} for chaining
 * @api public
 */


Request.prototype.accept = function (type) {
  this.set('Accept', request.types[type] || type);
  return this;
};
/**
 * Set Authorization field value with `user` and `pass`.
 *
 * @param {String} user
 * @param {String} [pass] optional in case of using 'bearer' as type
 * @param {Object} options with 'type' property 'auto', 'basic' or 'bearer' (default 'basic')
 * @return {Request} for chaining
 * @api public
 */


Request.prototype.auth = function (user, pass, options) {
  if (arguments.length === 1) pass = '';

  if (_typeof(pass) === 'object' && pass !== null) {
    // pass is optional and can be replaced with options
    options = pass;
    pass = '';
  }

  if (!options) {
    options = {
      type: typeof btoa === 'function' ? 'basic' : 'auto'
    };
  }

  var encoder = options.encoder ? options.encoder : function (string) {
    if (typeof btoa === 'function') {
      return btoa(string);
    }

    throw new Error('Cannot use basic auth, btoa is not a function');
  };
  return this._auth(user, pass, options, encoder);
};
/**
 * Add query-string `val`.
 *
 * Examples:
 *
 *   request.get('/shoes')
 *     .query('size=10')
 *     .query({ color: 'blue' })
 *
 * @param {Object|String} val
 * @return {Request} for chaining
 * @api public
 */


Request.prototype.query = function (value) {
  if (typeof value !== 'string') value = serialize(value);
  if (value) this._query.push(value);
  return this;
};
/**
 * Queue the given `file` as an attachment to the specified `field`,
 * with optional `options` (or filename).
 *
 * ``` js
 * request.post('/upload')
 *   .attach('content', new Blob(['<a id="a"><b id="b">hey!</b></a>'], { type: "text/html"}))
 *   .end(callback);
 * ```
 *
 * @param {String} field
 * @param {Blob|File} file
 * @param {String|Object} options
 * @return {Request} for chaining
 * @api public
 */


Request.prototype.attach = function (field, file, options) {
  if (file) {
    if (this._data) {
      throw new Error("superagent can't mix .send() and .attach()");
    }

    this._getFormData().append(field, file, options || file.name);
  }

  return this;
};

Request.prototype._getFormData = function () {
  if (!this._formData) {
    this._formData = new root.FormData();
  }

  return this._formData;
};
/**
 * Invoke the callback with `err` and `res`
 * and handle arity check.
 *
 * @param {Error} err
 * @param {Response} res
 * @api private
 */


Request.prototype.callback = function (error, res) {
  if (this._shouldRetry(error, res)) {
    return this._retry();
  }

  var fn = this._callback;
  this.clearTimeout();

  if (error) {
    if (this._maxRetries) error.retries = this._retries - 1;
    this.emit('error', error);
  }

  fn(error, res);
};
/**
 * Invoke callback with x-domain error.
 *
 * @api private
 */


Request.prototype.crossDomainError = function () {
  var error = new Error('Request has been terminated\nPossible causes: the network is offline, Origin is not allowed by Access-Control-Allow-Origin, the page is being unloaded, etc.');
  error.crossDomain = true;
  error.status = this.status;
  error.method = this.method;
  error.url = this.url;
  this.callback(error);
}; // This only warns, because the request is still likely to work


Request.prototype.agent = function () {
  console.warn('This is not supported in browser version of superagent');
  return this;
};

Request.prototype.ca = Request.prototype.agent;
Request.prototype.buffer = Request.prototype.ca; // This throws, because it can't send/receive data as expected

Request.prototype.write = function () {
  throw new Error('Streaming is not supported in browser version of superagent');
};

Request.prototype.pipe = Request.prototype.write;
/**
 * Check if `obj` is a host object,
 * we don't want to serialize these :)
 *
 * @param {Object} obj host object
 * @return {Boolean} is a host object
 * @api private
 */

Request.prototype._isHost = function (object) {
  // Native objects stringify to [object File], [object Blob], [object FormData], etc.
  return object && _typeof(object) === 'object' && !Array.isArray(object) && Object.prototype.toString.call(object) !== '[object Object]';
};
/**
 * Initiate request, invoking callback `fn(res)`
 * with an instanceof `Response`.
 *
 * @param {Function} fn
 * @return {Request} for chaining
 * @api public
 */


Request.prototype.end = function (fn) {
  if (this._endCalled) {
    console.warn('Warning: .end() was called twice. This is not supported in superagent');
  }

  this._endCalled = true; // store callback

  this._callback = fn || noop; // querystring

  this._finalizeQueryString();

  this._end();
};

Request.prototype._setUploadTimeout = function () {
  var self = this; // upload timeout it's wokrs only if deadline timeout is off

  if (this._uploadTimeout && !this._uploadTimeoutTimer) {
    this._uploadTimeoutTimer = setTimeout(function () {
      self._timeoutError('Upload timeout of ', self._uploadTimeout, 'ETIMEDOUT');
    }, this._uploadTimeout);
  }
}; // eslint-disable-next-line complexity


Request.prototype._end = function () {
  if (this._aborted) return this.callback(new Error('The request has been aborted even before .end() was called'));
  var self = this;
  this.xhr = request.getXHR();
  var xhr = this.xhr;
  var data = this._formData || this._data;

  this._setTimeouts(); // state change


  xhr.addEventListener('readystatechange', function () {
    var readyState = xhr.readyState;

    if (readyState >= 2 && self._responseTimeoutTimer) {
      clearTimeout(self._responseTimeoutTimer);
    }

    if (readyState !== 4) {
      return;
    } // In IE9, reads to any property (e.g. status) off of an aborted XHR will
    // result in the error "Could not complete the operation due to error c00c023f"


    var status;

    try {
      status = xhr.status;
    } catch (_unused) {
      status = 0;
    }

    if (!status) {
      if (self.timedout || self._aborted) return;
      return self.crossDomainError();
    }

    self.emit('end');
  }); // progress

  var handleProgress = function handleProgress(direction, e) {
    if (e.total > 0) {
      e.percent = e.loaded / e.total * 100;

      if (e.percent === 100) {
        clearTimeout(self._uploadTimeoutTimer);
      }
    }

    e.direction = direction;
    self.emit('progress', e);
  };

  if (this.hasListeners('progress')) {
    try {
      xhr.addEventListener('progress', handleProgress.bind(null, 'download'));

      if (xhr.upload) {
        xhr.upload.addEventListener('progress', handleProgress.bind(null, 'upload'));
      }
    } catch (_unused2) {// Accessing xhr.upload fails in IE from a web worker, so just pretend it doesn't exist.
      // Reported here:
      // https://connect.microsoft.com/IE/feedback/details/837245/xmlhttprequest-upload-throws-invalid-argument-when-used-from-web-worker-context
    }
  }

  if (xhr.upload) {
    this._setUploadTimeout();
  } // initiate request


  try {
    if (this.username && this.password) {
      xhr.open(this.method, this.url, true, this.username, this.password);
    } else {
      xhr.open(this.method, this.url, true);
    }
  } catch (err) {
    // see #1149
    return this.callback(err);
  } // CORS


  if (this._withCredentials) xhr.withCredentials = true; // body

  if (!this._formData && this.method !== 'GET' && this.method !== 'HEAD' && typeof data !== 'string' && !this._isHost(data)) {
    // serialize stuff
    var contentType = this._header['content-type'];

    var _serialize = this._serializer || request.serialize[contentType ? contentType.split(';')[0] : ''];

    if (!_serialize && isJSON(contentType)) {
      _serialize = request.serialize['application/json'];
    }

    if (_serialize) data = _serialize(data);
  } // set header fields


  for (var field in this.header) {
    if (this.header[field] === null) continue;
    if (hasOwn(this.header, field)) xhr.setRequestHeader(field, this.header[field]);
  }

  if (this._responseType) {
    xhr.responseType = this._responseType;
  } // send stuff


  this.emit('request', this); // IE11 xhr.send(undefined) sends 'undefined' string as POST payload (instead of nothing)
  // We need null here if data is undefined

  xhr.send(typeof data === 'undefined' ? null : data);
};

request.agent = function () {
  return new Agent();
};

var _loop = function _loop() {
  var method = _arr[_i];

  Agent.prototype[method.toLowerCase()] = function (url, fn) {
    var request_ = new request.Request(method, url);

    this._setDefaults(request_);

    if (fn) {
      request_.end(fn);
    }

    return request_;
  };
};

for (var _i = 0, _arr = ['GET', 'POST', 'OPTIONS', 'PATCH', 'PUT', 'DELETE']; _i < _arr.length; _i++) {
  _loop();
}

Agent.prototype.del = Agent.prototype.delete;
/**
 * GET `url` with optional callback `fn(res)`.
 *
 * @param {String} url
 * @param {Mixed|Function} [data] or fn
 * @param {Function} [fn]
 * @return {Request}
 * @api public
 */

request.get = function (url, data, fn) {
  var request_ = request('GET', url);

  if (typeof data === 'function') {
    fn = data;
    data = null;
  }

  if (data) request_.query(data);
  if (fn) request_.end(fn);
  return request_;
};
/**
 * HEAD `url` with optional callback `fn(res)`.
 *
 * @param {String} url
 * @param {Mixed|Function} [data] or fn
 * @param {Function} [fn]
 * @return {Request}
 * @api public
 */


request.head = function (url, data, fn) {
  var request_ = request('HEAD', url);

  if (typeof data === 'function') {
    fn = data;
    data = null;
  }

  if (data) request_.query(data);
  if (fn) request_.end(fn);
  return request_;
};
/**
 * OPTIONS query to `url` with optional callback `fn(res)`.
 *
 * @param {String} url
 * @param {Mixed|Function} [data] or fn
 * @param {Function} [fn]
 * @return {Request}
 * @api public
 */


request.options = function (url, data, fn) {
  var request_ = request('OPTIONS', url);

  if (typeof data === 'function') {
    fn = data;
    data = null;
  }

  if (data) request_.send(data);
  if (fn) request_.end(fn);
  return request_;
};
/**
 * DELETE `url` with optional `data` and callback `fn(res)`.
 *
 * @param {String} url
 * @param {Mixed} [data]
 * @param {Function} [fn]
 * @return {Request}
 * @api public
 */


function del(url, data, fn) {
  var request_ = request('DELETE', url);

  if (typeof data === 'function') {
    fn = data;
    data = null;
  }

  if (data) request_.send(data);
  if (fn) request_.end(fn);
  return request_;
}

request.del = del;
request.delete = del;
/**
 * PATCH `url` with optional `data` and callback `fn(res)`.
 *
 * @param {String} url
 * @param {Mixed} [data]
 * @param {Function} [fn]
 * @return {Request}
 * @api public
 */

request.patch = function (url, data, fn) {
  var request_ = request('PATCH', url);

  if (typeof data === 'function') {
    fn = data;
    data = null;
  }

  if (data) request_.send(data);
  if (fn) request_.end(fn);
  return request_;
};
/**
 * POST `url` with optional `data` and callback `fn(res)`.
 *
 * @param {String} url
 * @param {Mixed} [data]
 * @param {Function} [fn]
 * @return {Request}
 * @api public
 */


request.post = function (url, data, fn) {
  var request_ = request('POST', url);

  if (typeof data === 'function') {
    fn = data;
    data = null;
  }

  if (data) request_.send(data);
  if (fn) request_.end(fn);
  return request_;
};
/**
 * PUT `url` with optional `data` and callback `fn(res)`.
 *
 * @param {String} url
 * @param {Mixed|Function} [data] or fn
 * @param {Function} [fn]
 * @return {Request}
 * @api public
 */


request.put = function (url, data, fn) {
  var request_ = request('PUT', url);

  if (typeof data === 'function') {
    fn = data;
    data = null;
  }

  if (data) request_.send(data);
  if (fn) request_.end(fn);
  return request_;
};
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJuYW1lcyI6WyJyb290Iiwid2luZG93Iiwic2VsZiIsImNvbnNvbGUiLCJ3YXJuIiwiRW1pdHRlciIsInJlcXVpcmUiLCJzYWZlU3RyaW5naWZ5IiwicXMiLCJSZXF1ZXN0QmFzZSIsImlzT2JqZWN0IiwibWl4aW4iLCJoYXNPd24iLCJSZXNwb25zZUJhc2UiLCJBZ2VudCIsIm5vb3AiLCJtb2R1bGUiLCJleHBvcnRzIiwibWV0aG9kIiwidXJsIiwiUmVxdWVzdCIsImVuZCIsImFyZ3VtZW50cyIsImxlbmd0aCIsInJlcXVlc3QiLCJnZXRYSFIiLCJYTUxIdHRwUmVxdWVzdCIsImxvY2F0aW9uIiwicHJvdG9jb2wiLCJFcnJvciIsInRyaW0iLCJzIiwicmVwbGFjZSIsInNlcmlhbGl6ZSIsIm9iamVjdCIsInBhaXJzIiwia2V5IiwicHVzaEVuY29kZWRLZXlWYWx1ZVBhaXIiLCJqb2luIiwidmFsdWUiLCJ1bmRlZmluZWQiLCJwdXNoIiwiZW5jb2RlVVJJIiwiQXJyYXkiLCJpc0FycmF5IiwidiIsInN1YmtleSIsImVuY29kZVVSSUNvbXBvbmVudCIsInNlcmlhbGl6ZU9iamVjdCIsInBhcnNlU3RyaW5nIiwic3RyaW5nXyIsInNwbGl0IiwicGFpciIsInBvcyIsImkiLCJsZW5ndGhfIiwiaW5kZXhPZiIsImRlY29kZVVSSUNvbXBvbmVudCIsInNsaWNlIiwidHlwZXMiLCJodG1sIiwianNvbiIsInhtbCIsInVybGVuY29kZWQiLCJmb3JtIiwic3RyaW5naWZ5IiwicGFyc2UiLCJKU09OIiwicGFyc2VIZWFkZXIiLCJsaW5lcyIsImZpZWxkcyIsImluZGV4IiwibGluZSIsImZpZWxkIiwidG9Mb3dlckNhc2UiLCJpc0pTT04iLCJtaW1lIiwidGVzdCIsIlJlc3BvbnNlIiwicmVxdWVzdF8iLCJyZXEiLCJ4aHIiLCJ0ZXh0IiwicmVzcG9uc2VUeXBlIiwicmVzcG9uc2VUZXh0Iiwic3RhdHVzVGV4dCIsInN0YXR1cyIsIl9zZXRTdGF0dXNQcm9wZXJ0aWVzIiwiaGVhZGVycyIsImdldEFsbFJlc3BvbnNlSGVhZGVycyIsImhlYWRlciIsImdldFJlc3BvbnNlSGVhZGVyIiwiX3NldEhlYWRlclByb3BlcnRpZXMiLCJfcmVzcG9uc2VUeXBlIiwiYm9keSIsInJlc3BvbnNlIiwiX3BhcnNlQm9keSIsInByb3RvdHlwZSIsInR5cGUiLCJfcGFyc2VyIiwiT2JqZWN0IiwidG9FcnJvciIsIm1lc3NhZ2UiLCJlcnJvciIsIl9xdWVyeSIsIl9oZWFkZXIiLCJvbiIsInJlcyIsImVyciIsIm9yaWdpbmFsIiwicmF3UmVzcG9uc2UiLCJzdGF0dXNDb2RlIiwiY2FsbGJhY2siLCJlbWl0IiwibmV3X2Vycm9yIiwiX2lzUmVzcG9uc2VPSyIsInNldCIsImFjY2VwdCIsImF1dGgiLCJ1c2VyIiwicGFzcyIsIm9wdGlvbnMiLCJidG9hIiwiZW5jb2RlciIsInN0cmluZyIsIl9hdXRoIiwicXVlcnkiLCJhdHRhY2giLCJmaWxlIiwiX2RhdGEiLCJfZ2V0Rm9ybURhdGEiLCJhcHBlbmQiLCJuYW1lIiwiX2Zvcm1EYXRhIiwiRm9ybURhdGEiLCJfc2hvdWxkUmV0cnkiLCJfcmV0cnkiLCJmbiIsIl9jYWxsYmFjayIsImNsZWFyVGltZW91dCIsIl9tYXhSZXRyaWVzIiwicmV0cmllcyIsIl9yZXRyaWVzIiwiY3Jvc3NEb21haW5FcnJvciIsImNyb3NzRG9tYWluIiwiYWdlbnQiLCJjYSIsImJ1ZmZlciIsIndyaXRlIiwicGlwZSIsIl9pc0hvc3QiLCJ0b1N0cmluZyIsImNhbGwiLCJfZW5kQ2FsbGVkIiwiX2ZpbmFsaXplUXVlcnlTdHJpbmciLCJfZW5kIiwiX3NldFVwbG9hZFRpbWVvdXQiLCJfdXBsb2FkVGltZW91dCIsIl91cGxvYWRUaW1lb3V0VGltZXIiLCJzZXRUaW1lb3V0IiwiX3RpbWVvdXRFcnJvciIsIl9hYm9ydGVkIiwiZGF0YSIsIl9zZXRUaW1lb3V0cyIsImFkZEV2ZW50TGlzdGVuZXIiLCJyZWFkeVN0YXRlIiwiX3Jlc3BvbnNlVGltZW91dFRpbWVyIiwidGltZWRvdXQiLCJoYW5kbGVQcm9ncmVzcyIsImRpcmVjdGlvbiIsImUiLCJ0b3RhbCIsInBlcmNlbnQiLCJsb2FkZWQiLCJoYXNMaXN0ZW5lcnMiLCJiaW5kIiwidXBsb2FkIiwidXNlcm5hbWUiLCJwYXNzd29yZCIsIm9wZW4iLCJfd2l0aENyZWRlbnRpYWxzIiwid2l0aENyZWRlbnRpYWxzIiwiY29udGVudFR5cGUiLCJfc2VyaWFsaXplciIsInNldFJlcXVlc3RIZWFkZXIiLCJzZW5kIiwiX3NldERlZmF1bHRzIiwiZGVsIiwiZGVsZXRlIiwiZ2V0IiwiaGVhZCIsInBhdGNoIiwicG9zdCIsInB1dCJdLCJzb3VyY2VzIjpbIi4uL3NyYy9jbGllbnQuanMiXSwic291cmNlc0NvbnRlbnQiOlsiLyoqXG4gKiBSb290IHJlZmVyZW5jZSBmb3IgaWZyYW1lcy5cbiAqL1xuXG5sZXQgcm9vdDtcbmlmICh0eXBlb2Ygd2luZG93ICE9PSAndW5kZWZpbmVkJykge1xuICAvLyBCcm93c2VyIHdpbmRvd1xuICByb290ID0gd2luZG93O1xufSBlbHNlIGlmICh0eXBlb2Ygc2VsZiA9PT0gJ3VuZGVmaW5lZCcpIHtcbiAgLy8gT3RoZXIgZW52aXJvbm1lbnRzXG4gIGNvbnNvbGUud2FybihcbiAgICAnVXNpbmcgYnJvd3Nlci1vbmx5IHZlcnNpb24gb2Ygc3VwZXJhZ2VudCBpbiBub24tYnJvd3NlciBlbnZpcm9ubWVudCdcbiAgKTtcbiAgcm9vdCA9IHRoaXM7XG59IGVsc2Uge1xuICAvLyBXZWIgV29ya2VyXG4gIHJvb3QgPSBzZWxmO1xufVxuXG5jb25zdCBFbWl0dGVyID0gcmVxdWlyZSgnY29tcG9uZW50LWVtaXR0ZXInKTtcbmNvbnN0IHNhZmVTdHJpbmdpZnkgPSByZXF1aXJlKCdmYXN0LXNhZmUtc3RyaW5naWZ5Jyk7XG5jb25zdCBxcyA9IHJlcXVpcmUoJ3FzJyk7XG5jb25zdCBSZXF1ZXN0QmFzZSA9IHJlcXVpcmUoJy4vcmVxdWVzdC1iYXNlJyk7XG5jb25zdCB7IGlzT2JqZWN0LCBtaXhpbiwgaGFzT3duIH0gPSByZXF1aXJlKCcuL3V0aWxzJyk7XG5jb25zdCBSZXNwb25zZUJhc2UgPSByZXF1aXJlKCcuL3Jlc3BvbnNlLWJhc2UnKTtcbmNvbnN0IEFnZW50ID0gcmVxdWlyZSgnLi9hZ2VudC1iYXNlJyk7XG5cbi8qKlxuICogTm9vcC5cbiAqL1xuXG5mdW5jdGlvbiBub29wKCkge31cblxuLyoqXG4gKiBFeHBvc2UgYHJlcXVlc3RgLlxuICovXG5cbm1vZHVsZS5leHBvcnRzID0gZnVuY3Rpb24gKG1ldGhvZCwgdXJsKSB7XG4gIC8vIGNhbGxiYWNrXG4gIGlmICh0eXBlb2YgdXJsID09PSAnZnVuY3Rpb24nKSB7XG4gICAgcmV0dXJuIG5ldyBleHBvcnRzLlJlcXVlc3QoJ0dFVCcsIG1ldGhvZCkuZW5kKHVybCk7XG4gIH1cblxuICAvLyB1cmwgZmlyc3RcbiAgaWYgKGFyZ3VtZW50cy5sZW5ndGggPT09IDEpIHtcbiAgICByZXR1cm4gbmV3IGV4cG9ydHMuUmVxdWVzdCgnR0VUJywgbWV0aG9kKTtcbiAgfVxuXG4gIHJldHVybiBuZXcgZXhwb3J0cy5SZXF1ZXN0KG1ldGhvZCwgdXJsKTtcbn07XG5cbmV4cG9ydHMgPSBtb2R1bGUuZXhwb3J0cztcblxuY29uc3QgcmVxdWVzdCA9IGV4cG9ydHM7XG5cbmV4cG9ydHMuUmVxdWVzdCA9IFJlcXVlc3Q7XG5cbi8qKlxuICogRGV0ZXJtaW5lIFhIUi5cbiAqL1xuXG5yZXF1ZXN0LmdldFhIUiA9ICgpID0+IHtcbiAgaWYgKFxuICAgIHJvb3QuWE1MSHR0cFJlcXVlc3QgJiZcbiAgICAoIXJvb3QubG9jYXRpb24gfHwgcm9vdC5sb2NhdGlvbi5wcm90b2NvbCAhPT0gJ2ZpbGU6JylcbiAgKSB7XG4gICAgcmV0dXJuIG5ldyBYTUxIdHRwUmVxdWVzdCgpO1xuICB9XG5cbiAgdGhyb3cgbmV3IEVycm9yKCdCcm93c2VyLW9ubHkgdmVyc2lvbiBvZiBzdXBlcmFnZW50IGNvdWxkIG5vdCBmaW5kIFhIUicpO1xufTtcblxuLyoqXG4gKiBSZW1vdmVzIGxlYWRpbmcgYW5kIHRyYWlsaW5nIHdoaXRlc3BhY2UsIGFkZGVkIHRvIHN1cHBvcnQgSUUuXG4gKlxuICogQHBhcmFtIHtTdHJpbmd9IHNcbiAqIEByZXR1cm4ge1N0cmluZ31cbiAqIEBhcGkgcHJpdmF0ZVxuICovXG5cbmNvbnN0IHRyaW0gPSAnJy50cmltID8gKHMpID0+IHMudHJpbSgpIDogKHMpID0+IHMucmVwbGFjZSgvKF5cXHMqfFxccyokKS9nLCAnJyk7XG5cbi8qKlxuICogU2VyaWFsaXplIHRoZSBnaXZlbiBgb2JqYC5cbiAqXG4gKiBAcGFyYW0ge09iamVjdH0gb2JqXG4gKiBAcmV0dXJuIHtTdHJpbmd9XG4gKiBAYXBpIHByaXZhdGVcbiAqL1xuXG5mdW5jdGlvbiBzZXJpYWxpemUob2JqZWN0KSB7XG4gIGlmICghaXNPYmplY3Qob2JqZWN0KSkgcmV0dXJuIG9iamVjdDtcbiAgY29uc3QgcGFpcnMgPSBbXTtcbiAgZm9yIChjb25zdCBrZXkgaW4gb2JqZWN0KSB7XG4gICAgaWYgKGhhc093bihvYmplY3QsIGtleSkpIHB1c2hFbmNvZGVkS2V5VmFsdWVQYWlyKHBhaXJzLCBrZXksIG9iamVjdFtrZXldKTtcbiAgfVxuXG4gIHJldHVybiBwYWlycy5qb2luKCcmJyk7XG59XG5cbi8qKlxuICogSGVscHMgJ3NlcmlhbGl6ZScgd2l0aCBzZXJpYWxpemluZyBhcnJheXMuXG4gKiBNdXRhdGVzIHRoZSBwYWlycyBhcnJheS5cbiAqXG4gKiBAcGFyYW0ge0FycmF5fSBwYWlyc1xuICogQHBhcmFtIHtTdHJpbmd9IGtleVxuICogQHBhcmFtIHtNaXhlZH0gdmFsXG4gKi9cblxuZnVuY3Rpb24gcHVzaEVuY29kZWRLZXlWYWx1ZVBhaXIocGFpcnMsIGtleSwgdmFsdWUpIHtcbiAgaWYgKHZhbHVlID09PSB1bmRlZmluZWQpIHJldHVybjtcbiAgaWYgKHZhbHVlID09PSBudWxsKSB7XG4gICAgcGFpcnMucHVzaChlbmNvZGVVUkkoa2V5KSk7XG4gICAgcmV0dXJuO1xuICB9XG5cbiAgaWYgKEFycmF5LmlzQXJyYXkodmFsdWUpKSB7XG4gICAgZm9yIChjb25zdCB2IG9mIHZhbHVlKSB7XG4gICAgICBwdXNoRW5jb2RlZEtleVZhbHVlUGFpcihwYWlycywga2V5LCB2KTtcbiAgICB9XG4gIH0gZWxzZSBpZiAoaXNPYmplY3QodmFsdWUpKSB7XG4gICAgZm9yIChjb25zdCBzdWJrZXkgaW4gdmFsdWUpIHtcbiAgICAgIGlmIChoYXNPd24odmFsdWUsIHN1YmtleSkpXG4gICAgICAgIHB1c2hFbmNvZGVkS2V5VmFsdWVQYWlyKHBhaXJzLCBgJHtrZXl9WyR7c3Via2V5fV1gLCB2YWx1ZVtzdWJrZXldKTtcbiAgICB9XG4gIH0gZWxzZSB7XG4gICAgcGFpcnMucHVzaChlbmNvZGVVUkkoa2V5KSArICc9JyArIGVuY29kZVVSSUNvbXBvbmVudCh2YWx1ZSkpO1xuICB9XG59XG5cbi8qKlxuICogRXhwb3NlIHNlcmlhbGl6YXRpb24gbWV0aG9kLlxuICovXG5cbnJlcXVlc3Quc2VyaWFsaXplT2JqZWN0ID0gc2VyaWFsaXplO1xuXG4vKipcbiAqIFBhcnNlIHRoZSBnaXZlbiB4LXd3dy1mb3JtLXVybGVuY29kZWQgYHN0cmAuXG4gKlxuICogQHBhcmFtIHtTdHJpbmd9IHN0clxuICogQHJldHVybiB7T2JqZWN0fVxuICogQGFwaSBwcml2YXRlXG4gKi9cblxuZnVuY3Rpb24gcGFyc2VTdHJpbmcoc3RyaW5nXykge1xuICBjb25zdCBvYmplY3QgPSB7fTtcbiAgY29uc3QgcGFpcnMgPSBzdHJpbmdfLnNwbGl0KCcmJyk7XG4gIGxldCBwYWlyO1xuICBsZXQgcG9zO1xuXG4gIGZvciAobGV0IGkgPSAwLCBsZW5ndGhfID0gcGFpcnMubGVuZ3RoOyBpIDwgbGVuZ3RoXzsgKytpKSB7XG4gICAgcGFpciA9IHBhaXJzW2ldO1xuICAgIHBvcyA9IHBhaXIuaW5kZXhPZignPScpO1xuICAgIGlmIChwb3MgPT09IC0xKSB7XG4gICAgICBvYmplY3RbZGVjb2RlVVJJQ29tcG9uZW50KHBhaXIpXSA9ICcnO1xuICAgIH0gZWxzZSB7XG4gICAgICBvYmplY3RbZGVjb2RlVVJJQ29tcG9uZW50KHBhaXIuc2xpY2UoMCwgcG9zKSldID0gZGVjb2RlVVJJQ29tcG9uZW50KFxuICAgICAgICBwYWlyLnNsaWNlKHBvcyArIDEpXG4gICAgICApO1xuICAgIH1cbiAgfVxuXG4gIHJldHVybiBvYmplY3Q7XG59XG5cbi8qKlxuICogRXhwb3NlIHBhcnNlci5cbiAqL1xuXG5yZXF1ZXN0LnBhcnNlU3RyaW5nID0gcGFyc2VTdHJpbmc7XG5cbi8qKlxuICogRGVmYXVsdCBNSU1FIHR5cGUgbWFwLlxuICpcbiAqICAgICBzdXBlcmFnZW50LnR5cGVzLnhtbCA9ICdhcHBsaWNhdGlvbi94bWwnO1xuICpcbiAqL1xuXG5yZXF1ZXN0LnR5cGVzID0ge1xuICBodG1sOiAndGV4dC9odG1sJyxcbiAganNvbjogJ2FwcGxpY2F0aW9uL2pzb24nLFxuICB4bWw6ICd0ZXh0L3htbCcsXG4gIHVybGVuY29kZWQ6ICdhcHBsaWNhdGlvbi94LXd3dy1mb3JtLXVybGVuY29kZWQnLFxuICBmb3JtOiAnYXBwbGljYXRpb24veC13d3ctZm9ybS11cmxlbmNvZGVkJyxcbiAgJ2Zvcm0tZGF0YSc6ICdhcHBsaWNhdGlvbi94LXd3dy1mb3JtLXVybGVuY29kZWQnXG59O1xuXG4vKipcbiAqIERlZmF1bHQgc2VyaWFsaXphdGlvbiBtYXAuXG4gKlxuICogICAgIHN1cGVyYWdlbnQuc2VyaWFsaXplWydhcHBsaWNhdGlvbi94bWwnXSA9IGZ1bmN0aW9uKG9iail7XG4gKiAgICAgICByZXR1cm4gJ2dlbmVyYXRlZCB4bWwgaGVyZSc7XG4gKiAgICAgfTtcbiAqXG4gKi9cblxucmVxdWVzdC5zZXJpYWxpemUgPSB7XG4gICdhcHBsaWNhdGlvbi94LXd3dy1mb3JtLXVybGVuY29kZWQnOiBxcy5zdHJpbmdpZnksXG4gICdhcHBsaWNhdGlvbi9qc29uJzogc2FmZVN0cmluZ2lmeVxufTtcblxuLyoqXG4gKiBEZWZhdWx0IHBhcnNlcnMuXG4gKlxuICogICAgIHN1cGVyYWdlbnQucGFyc2VbJ2FwcGxpY2F0aW9uL3htbCddID0gZnVuY3Rpb24oc3RyKXtcbiAqICAgICAgIHJldHVybiB7IG9iamVjdCBwYXJzZWQgZnJvbSBzdHIgfTtcbiAqICAgICB9O1xuICpcbiAqL1xuXG5yZXF1ZXN0LnBhcnNlID0ge1xuICAnYXBwbGljYXRpb24veC13d3ctZm9ybS11cmxlbmNvZGVkJzogcGFyc2VTdHJpbmcsXG4gICdhcHBsaWNhdGlvbi9qc29uJzogSlNPTi5wYXJzZVxufTtcblxuLyoqXG4gKiBQYXJzZSB0aGUgZ2l2ZW4gaGVhZGVyIGBzdHJgIGludG9cbiAqIGFuIG9iamVjdCBjb250YWluaW5nIHRoZSBtYXBwZWQgZmllbGRzLlxuICpcbiAqIEBwYXJhbSB7U3RyaW5nfSBzdHJcbiAqIEByZXR1cm4ge09iamVjdH1cbiAqIEBhcGkgcHJpdmF0ZVxuICovXG5cbmZ1bmN0aW9uIHBhcnNlSGVhZGVyKHN0cmluZ18pIHtcbiAgY29uc3QgbGluZXMgPSBzdHJpbmdfLnNwbGl0KC9cXHI/XFxuLyk7XG4gIGNvbnN0IGZpZWxkcyA9IHt9O1xuICBsZXQgaW5kZXg7XG4gIGxldCBsaW5lO1xuICBsZXQgZmllbGQ7XG4gIGxldCB2YWx1ZTtcblxuICBmb3IgKGxldCBpID0gMCwgbGVuZ3RoXyA9IGxpbmVzLmxlbmd0aDsgaSA8IGxlbmd0aF87ICsraSkge1xuICAgIGxpbmUgPSBsaW5lc1tpXTtcbiAgICBpbmRleCA9IGxpbmUuaW5kZXhPZignOicpO1xuICAgIGlmIChpbmRleCA9PT0gLTEpIHtcbiAgICAgIC8vIGNvdWxkIGJlIGVtcHR5IGxpbmUsIGp1c3Qgc2tpcCBpdFxuICAgICAgY29udGludWU7XG4gICAgfVxuXG4gICAgZmllbGQgPSBsaW5lLnNsaWNlKDAsIGluZGV4KS50b0xvd2VyQ2FzZSgpO1xuICAgIHZhbHVlID0gdHJpbShsaW5lLnNsaWNlKGluZGV4ICsgMSkpO1xuICAgIGZpZWxkc1tmaWVsZF0gPSB2YWx1ZTtcbiAgfVxuXG4gIHJldHVybiBmaWVsZHM7XG59XG5cbi8qKlxuICogQ2hlY2sgaWYgYG1pbWVgIGlzIGpzb24gb3IgaGFzICtqc29uIHN0cnVjdHVyZWQgc3ludGF4IHN1ZmZpeC5cbiAqXG4gKiBAcGFyYW0ge1N0cmluZ30gbWltZVxuICogQHJldHVybiB7Qm9vbGVhbn1cbiAqIEBhcGkgcHJpdmF0ZVxuICovXG5cbmZ1bmN0aW9uIGlzSlNPTihtaW1lKSB7XG4gIC8vIHNob3VsZCBtYXRjaCAvanNvbiBvciAranNvblxuICAvLyBidXQgbm90IC9qc29uLXNlcVxuICByZXR1cm4gL1svK11qc29uKCR8W14tXFx3XSkvaS50ZXN0KG1pbWUpO1xufVxuXG4vKipcbiAqIEluaXRpYWxpemUgYSBuZXcgYFJlc3BvbnNlYCB3aXRoIHRoZSBnaXZlbiBgeGhyYC5cbiAqXG4gKiAgLSBzZXQgZmxhZ3MgKC5vaywgLmVycm9yLCBldGMpXG4gKiAgLSBwYXJzZSBoZWFkZXJcbiAqXG4gKiBFeGFtcGxlczpcbiAqXG4gKiAgQWxpYXNpbmcgYHN1cGVyYWdlbnRgIGFzIGByZXF1ZXN0YCBpcyBuaWNlOlxuICpcbiAqICAgICAgcmVxdWVzdCA9IHN1cGVyYWdlbnQ7XG4gKlxuICogIFdlIGNhbiB1c2UgdGhlIHByb21pc2UtbGlrZSBBUEksIG9yIHBhc3MgY2FsbGJhY2tzOlxuICpcbiAqICAgICAgcmVxdWVzdC5nZXQoJy8nKS5lbmQoZnVuY3Rpb24ocmVzKXt9KTtcbiAqICAgICAgcmVxdWVzdC5nZXQoJy8nLCBmdW5jdGlvbihyZXMpe30pO1xuICpcbiAqICBTZW5kaW5nIGRhdGEgY2FuIGJlIGNoYWluZWQ6XG4gKlxuICogICAgICByZXF1ZXN0XG4gKiAgICAgICAgLnBvc3QoJy91c2VyJylcbiAqICAgICAgICAuc2VuZCh7IG5hbWU6ICd0aicgfSlcbiAqICAgICAgICAuZW5kKGZ1bmN0aW9uKHJlcyl7fSk7XG4gKlxuICogIE9yIHBhc3NlZCB0byBgLnNlbmQoKWA6XG4gKlxuICogICAgICByZXF1ZXN0XG4gKiAgICAgICAgLnBvc3QoJy91c2VyJylcbiAqICAgICAgICAuc2VuZCh7IG5hbWU6ICd0aicgfSwgZnVuY3Rpb24ocmVzKXt9KTtcbiAqXG4gKiAgT3IgcGFzc2VkIHRvIGAucG9zdCgpYDpcbiAqXG4gKiAgICAgIHJlcXVlc3RcbiAqICAgICAgICAucG9zdCgnL3VzZXInLCB7IG5hbWU6ICd0aicgfSlcbiAqICAgICAgICAuZW5kKGZ1bmN0aW9uKHJlcyl7fSk7XG4gKlxuICogT3IgZnVydGhlciByZWR1Y2VkIHRvIGEgc2luZ2xlIGNhbGwgZm9yIHNpbXBsZSBjYXNlczpcbiAqXG4gKiAgICAgIHJlcXVlc3RcbiAqICAgICAgICAucG9zdCgnL3VzZXInLCB7IG5hbWU6ICd0aicgfSwgZnVuY3Rpb24ocmVzKXt9KTtcbiAqXG4gKiBAcGFyYW0ge1hNTEhUVFBSZXF1ZXN0fSB4aHJcbiAqIEBwYXJhbSB7T2JqZWN0fSBvcHRpb25zXG4gKiBAYXBpIHByaXZhdGVcbiAqL1xuXG5mdW5jdGlvbiBSZXNwb25zZShyZXF1ZXN0Xykge1xuICB0aGlzLnJlcSA9IHJlcXVlc3RfO1xuICB0aGlzLnhociA9IHRoaXMucmVxLnhocjtcbiAgLy8gcmVzcG9uc2VUZXh0IGlzIGFjY2Vzc2libGUgb25seSBpZiByZXNwb25zZVR5cGUgaXMgJycgb3IgJ3RleHQnIGFuZCBvbiBvbGRlciBicm93c2Vyc1xuICB0aGlzLnRleHQgPVxuICAgICh0aGlzLnJlcS5tZXRob2QgIT09ICdIRUFEJyAmJlxuICAgICAgKHRoaXMueGhyLnJlc3BvbnNlVHlwZSA9PT0gJycgfHwgdGhpcy54aHIucmVzcG9uc2VUeXBlID09PSAndGV4dCcpKSB8fFxuICAgIHR5cGVvZiB0aGlzLnhoci5yZXNwb25zZVR5cGUgPT09ICd1bmRlZmluZWQnXG4gICAgICA/IHRoaXMueGhyLnJlc3BvbnNlVGV4dFxuICAgICAgOiBudWxsO1xuICB0aGlzLnN0YXR1c1RleHQgPSB0aGlzLnJlcS54aHIuc3RhdHVzVGV4dDtcbiAgbGV0IHsgc3RhdHVzIH0gPSB0aGlzLnhocjtcbiAgLy8gaGFuZGxlIElFOSBidWc6IGh0dHA6Ly9zdGFja292ZXJmbG93LmNvbS9xdWVzdGlvbnMvMTAwNDY5NzIvbXNpZS1yZXR1cm5zLXN0YXR1cy1jb2RlLW9mLTEyMjMtZm9yLWFqYXgtcmVxdWVzdFxuICBpZiAoc3RhdHVzID09PSAxMjIzKSB7XG4gICAgc3RhdHVzID0gMjA0O1xuICB9XG5cbiAgdGhpcy5fc2V0U3RhdHVzUHJvcGVydGllcyhzdGF0dXMpO1xuICB0aGlzLmhlYWRlcnMgPSBwYXJzZUhlYWRlcih0aGlzLnhoci5nZXRBbGxSZXNwb25zZUhlYWRlcnMoKSk7XG4gIHRoaXMuaGVhZGVyID0gdGhpcy5oZWFkZXJzO1xuICAvLyBnZXRBbGxSZXNwb25zZUhlYWRlcnMgc29tZXRpbWVzIGZhbHNlbHkgcmV0dXJucyBcIlwiIGZvciBDT1JTIHJlcXVlc3RzLCBidXRcbiAgLy8gZ2V0UmVzcG9uc2VIZWFkZXIgc3RpbGwgd29ya3MuIHNvIHdlIGdldCBjb250ZW50LXR5cGUgZXZlbiBpZiBnZXR0aW5nXG4gIC8vIG90aGVyIGhlYWRlcnMgZmFpbHMuXG4gIHRoaXMuaGVhZGVyWydjb250ZW50LXR5cGUnXSA9IHRoaXMueGhyLmdldFJlc3BvbnNlSGVhZGVyKCdjb250ZW50LXR5cGUnKTtcbiAgdGhpcy5fc2V0SGVhZGVyUHJvcGVydGllcyh0aGlzLmhlYWRlcik7XG5cbiAgaWYgKHRoaXMudGV4dCA9PT0gbnVsbCAmJiByZXF1ZXN0Xy5fcmVzcG9uc2VUeXBlKSB7XG4gICAgdGhpcy5ib2R5ID0gdGhpcy54aHIucmVzcG9uc2U7XG4gIH0gZWxzZSB7XG4gICAgdGhpcy5ib2R5ID1cbiAgICAgIHRoaXMucmVxLm1ldGhvZCA9PT0gJ0hFQUQnXG4gICAgICAgID8gbnVsbFxuICAgICAgICA6IHRoaXMuX3BhcnNlQm9keSh0aGlzLnRleHQgPyB0aGlzLnRleHQgOiB0aGlzLnhoci5yZXNwb25zZSk7XG4gIH1cbn1cblxubWl4aW4oUmVzcG9uc2UucHJvdG90eXBlLCBSZXNwb25zZUJhc2UucHJvdG90eXBlKTtcblxuLyoqXG4gKiBQYXJzZSB0aGUgZ2l2ZW4gYm9keSBgc3RyYC5cbiAqXG4gKiBVc2VkIGZvciBhdXRvLXBhcnNpbmcgb2YgYm9kaWVzLiBQYXJzZXJzXG4gKiBhcmUgZGVmaW5lZCBvbiB0aGUgYHN1cGVyYWdlbnQucGFyc2VgIG9iamVjdC5cbiAqXG4gKiBAcGFyYW0ge1N0cmluZ30gc3RyXG4gKiBAcmV0dXJuIHtNaXhlZH1cbiAqIEBhcGkgcHJpdmF0ZVxuICovXG5cblJlc3BvbnNlLnByb3RvdHlwZS5fcGFyc2VCb2R5ID0gZnVuY3Rpb24gKHN0cmluZ18pIHtcbiAgbGV0IHBhcnNlID0gcmVxdWVzdC5wYXJzZVt0aGlzLnR5cGVdO1xuICBpZiAodGhpcy5yZXEuX3BhcnNlcikge1xuICAgIHJldHVybiB0aGlzLnJlcS5fcGFyc2VyKHRoaXMsIHN0cmluZ18pO1xuICB9XG5cbiAgaWYgKCFwYXJzZSAmJiBpc0pTT04odGhpcy50eXBlKSkge1xuICAgIHBhcnNlID0gcmVxdWVzdC5wYXJzZVsnYXBwbGljYXRpb24vanNvbiddO1xuICB9XG5cbiAgcmV0dXJuIHBhcnNlICYmIHN0cmluZ18gJiYgKHN0cmluZ18ubGVuZ3RoID4gMCB8fCBzdHJpbmdfIGluc3RhbmNlb2YgT2JqZWN0KVxuICAgID8gcGFyc2Uoc3RyaW5nXylcbiAgICA6IG51bGw7XG59O1xuXG4vKipcbiAqIFJldHVybiBhbiBgRXJyb3JgIHJlcHJlc2VudGF0aXZlIG9mIHRoaXMgcmVzcG9uc2UuXG4gKlxuICogQHJldHVybiB7RXJyb3J9XG4gKiBAYXBpIHB1YmxpY1xuICovXG5cblJlc3BvbnNlLnByb3RvdHlwZS50b0Vycm9yID0gZnVuY3Rpb24gKCkge1xuICBjb25zdCB7IHJlcSB9ID0gdGhpcztcbiAgY29uc3QgeyBtZXRob2QgfSA9IHJlcTtcbiAgY29uc3QgeyB1cmwgfSA9IHJlcTtcblxuICBjb25zdCBtZXNzYWdlID0gYGNhbm5vdCAke21ldGhvZH0gJHt1cmx9ICgke3RoaXMuc3RhdHVzfSlgO1xuICBjb25zdCBlcnJvciA9IG5ldyBFcnJvcihtZXNzYWdlKTtcbiAgZXJyb3Iuc3RhdHVzID0gdGhpcy5zdGF0dXM7XG4gIGVycm9yLm1ldGhvZCA9IG1ldGhvZDtcbiAgZXJyb3IudXJsID0gdXJsO1xuXG4gIHJldHVybiBlcnJvcjtcbn07XG5cbi8qKlxuICogRXhwb3NlIGBSZXNwb25zZWAuXG4gKi9cblxucmVxdWVzdC5SZXNwb25zZSA9IFJlc3BvbnNlO1xuXG4vKipcbiAqIEluaXRpYWxpemUgYSBuZXcgYFJlcXVlc3RgIHdpdGggdGhlIGdpdmVuIGBtZXRob2RgIGFuZCBgdXJsYC5cbiAqXG4gKiBAcGFyYW0ge1N0cmluZ30gbWV0aG9kXG4gKiBAcGFyYW0ge1N0cmluZ30gdXJsXG4gKiBAYXBpIHB1YmxpY1xuICovXG5cbmZ1bmN0aW9uIFJlcXVlc3QobWV0aG9kLCB1cmwpIHtcbiAgY29uc3Qgc2VsZiA9IHRoaXM7XG4gIHRoaXMuX3F1ZXJ5ID0gdGhpcy5fcXVlcnkgfHwgW107XG4gIHRoaXMubWV0aG9kID0gbWV0aG9kO1xuICB0aGlzLnVybCA9IHVybDtcbiAgdGhpcy5oZWFkZXIgPSB7fTsgLy8gcHJlc2VydmVzIGhlYWRlciBuYW1lIGNhc2VcbiAgdGhpcy5faGVhZGVyID0ge307IC8vIGNvZXJjZXMgaGVhZGVyIG5hbWVzIHRvIGxvd2VyY2FzZVxuICB0aGlzLm9uKCdlbmQnLCAoKSA9PiB7XG4gICAgbGV0IGVycm9yID0gbnVsbDtcbiAgICBsZXQgcmVzID0gbnVsbDtcblxuICAgIHRyeSB7XG4gICAgICByZXMgPSBuZXcgUmVzcG9uc2Uoc2VsZik7XG4gICAgfSBjYXRjaCAoZXJyKSB7XG4gICAgICBlcnJvciA9IG5ldyBFcnJvcignUGFyc2VyIGlzIHVuYWJsZSB0byBwYXJzZSB0aGUgcmVzcG9uc2UnKTtcbiAgICAgIGVycm9yLnBhcnNlID0gdHJ1ZTtcbiAgICAgIGVycm9yLm9yaWdpbmFsID0gZXJyO1xuICAgICAgLy8gaXNzdWUgIzY3NTogcmV0dXJuIHRoZSByYXcgcmVzcG9uc2UgaWYgdGhlIHJlc3BvbnNlIHBhcnNpbmcgZmFpbHNcbiAgICAgIGlmIChzZWxmLnhocikge1xuICAgICAgICAvLyBpZTkgZG9lc24ndCBoYXZlICdyZXNwb25zZScgcHJvcGVydHlcbiAgICAgICAgZXJyb3IucmF3UmVzcG9uc2UgPVxuICAgICAgICAgIHR5cGVvZiBzZWxmLnhoci5yZXNwb25zZVR5cGUgPT09ICd1bmRlZmluZWQnXG4gICAgICAgICAgICA/IHNlbGYueGhyLnJlc3BvbnNlVGV4dFxuICAgICAgICAgICAgOiBzZWxmLnhoci5yZXNwb25zZTtcbiAgICAgICAgLy8gaXNzdWUgIzg3NjogcmV0dXJuIHRoZSBodHRwIHN0YXR1cyBjb2RlIGlmIHRoZSByZXNwb25zZSBwYXJzaW5nIGZhaWxzXG4gICAgICAgIGVycm9yLnN0YXR1cyA9IHNlbGYueGhyLnN0YXR1cyA/IHNlbGYueGhyLnN0YXR1cyA6IG51bGw7XG4gICAgICAgIGVycm9yLnN0YXR1c0NvZGUgPSBlcnJvci5zdGF0dXM7IC8vIGJhY2t3YXJkcy1jb21wYXQgb25seVxuICAgICAgfSBlbHNlIHtcbiAgICAgICAgZXJyb3IucmF3UmVzcG9uc2UgPSBudWxsO1xuICAgICAgICBlcnJvci5zdGF0dXMgPSBudWxsO1xuICAgICAgfVxuXG4gICAgICByZXR1cm4gc2VsZi5jYWxsYmFjayhlcnJvcik7XG4gICAgfVxuXG4gICAgc2VsZi5lbWl0KCdyZXNwb25zZScsIHJlcyk7XG5cbiAgICBsZXQgbmV3X2Vycm9yO1xuICAgIHRyeSB7XG4gICAgICBpZiAoIXNlbGYuX2lzUmVzcG9uc2VPSyhyZXMpKSB7XG4gICAgICAgIG5ld19lcnJvciA9IG5ldyBFcnJvcihcbiAgICAgICAgICByZXMuc3RhdHVzVGV4dCB8fCByZXMudGV4dCB8fCAnVW5zdWNjZXNzZnVsIEhUVFAgcmVzcG9uc2UnXG4gICAgICAgICk7XG4gICAgICB9XG4gICAgfSBjYXRjaCAoZXJyKSB7XG4gICAgICBuZXdfZXJyb3IgPSBlcnI7IC8vIG9rKCkgY2FsbGJhY2sgY2FuIHRocm93XG4gICAgfVxuXG4gICAgLy8gIzEwMDAgZG9uJ3QgY2F0Y2ggZXJyb3JzIGZyb20gdGhlIGNhbGxiYWNrIHRvIGF2b2lkIGRvdWJsZSBjYWxsaW5nIGl0XG4gICAgaWYgKG5ld19lcnJvcikge1xuICAgICAgbmV3X2Vycm9yLm9yaWdpbmFsID0gZXJyb3I7XG4gICAgICBuZXdfZXJyb3IucmVzcG9uc2UgPSByZXM7XG4gICAgICBuZXdfZXJyb3Iuc3RhdHVzID0gbmV3X2Vycm9yLnN0YXR1cyB8fCByZXMuc3RhdHVzO1xuICAgICAgc2VsZi5jYWxsYmFjayhuZXdfZXJyb3IsIHJlcyk7XG4gICAgfSBlbHNlIHtcbiAgICAgIHNlbGYuY2FsbGJhY2sobnVsbCwgcmVzKTtcbiAgICB9XG4gIH0pO1xufVxuXG4vKipcbiAqIE1peGluIGBFbWl0dGVyYCBhbmQgYFJlcXVlc3RCYXNlYC5cbiAqL1xuXG4vLyBlc2xpbnQtZGlzYWJsZS1uZXh0LWxpbmUgbmV3LWNhcFxuRW1pdHRlcihSZXF1ZXN0LnByb3RvdHlwZSk7XG5cbm1peGluKFJlcXVlc3QucHJvdG90eXBlLCBSZXF1ZXN0QmFzZS5wcm90b3R5cGUpO1xuXG4vKipcbiAqIFNldCBDb250ZW50LVR5cGUgdG8gYHR5cGVgLCBtYXBwaW5nIHZhbHVlcyBmcm9tIGByZXF1ZXN0LnR5cGVzYC5cbiAqXG4gKiBFeGFtcGxlczpcbiAqXG4gKiAgICAgIHN1cGVyYWdlbnQudHlwZXMueG1sID0gJ2FwcGxpY2F0aW9uL3htbCc7XG4gKlxuICogICAgICByZXF1ZXN0LnBvc3QoJy8nKVxuICogICAgICAgIC50eXBlKCd4bWwnKVxuICogICAgICAgIC5zZW5kKHhtbHN0cmluZylcbiAqICAgICAgICAuZW5kKGNhbGxiYWNrKTtcbiAqXG4gKiAgICAgIHJlcXVlc3QucG9zdCgnLycpXG4gKiAgICAgICAgLnR5cGUoJ2FwcGxpY2F0aW9uL3htbCcpXG4gKiAgICAgICAgLnNlbmQoeG1sc3RyaW5nKVxuICogICAgICAgIC5lbmQoY2FsbGJhY2spO1xuICpcbiAqIEBwYXJhbSB7U3RyaW5nfSB0eXBlXG4gKiBAcmV0dXJuIHtSZXF1ZXN0fSBmb3IgY2hhaW5pbmdcbiAqIEBhcGkgcHVibGljXG4gKi9cblxuUmVxdWVzdC5wcm90b3R5cGUudHlwZSA9IGZ1bmN0aW9uICh0eXBlKSB7XG4gIHRoaXMuc2V0KCdDb250ZW50LVR5cGUnLCByZXF1ZXN0LnR5cGVzW3R5cGVdIHx8IHR5cGUpO1xuICByZXR1cm4gdGhpcztcbn07XG5cbi8qKlxuICogU2V0IEFjY2VwdCB0byBgdHlwZWAsIG1hcHBpbmcgdmFsdWVzIGZyb20gYHJlcXVlc3QudHlwZXNgLlxuICpcbiAqIEV4YW1wbGVzOlxuICpcbiAqICAgICAgc3VwZXJhZ2VudC50eXBlcy5qc29uID0gJ2FwcGxpY2F0aW9uL2pzb24nO1xuICpcbiAqICAgICAgcmVxdWVzdC5nZXQoJy9hZ2VudCcpXG4gKiAgICAgICAgLmFjY2VwdCgnanNvbicpXG4gKiAgICAgICAgLmVuZChjYWxsYmFjayk7XG4gKlxuICogICAgICByZXF1ZXN0LmdldCgnL2FnZW50JylcbiAqICAgICAgICAuYWNjZXB0KCdhcHBsaWNhdGlvbi9qc29uJylcbiAqICAgICAgICAuZW5kKGNhbGxiYWNrKTtcbiAqXG4gKiBAcGFyYW0ge1N0cmluZ30gYWNjZXB0XG4gKiBAcmV0dXJuIHtSZXF1ZXN0fSBmb3IgY2hhaW5pbmdcbiAqIEBhcGkgcHVibGljXG4gKi9cblxuUmVxdWVzdC5wcm90b3R5cGUuYWNjZXB0ID0gZnVuY3Rpb24gKHR5cGUpIHtcbiAgdGhpcy5zZXQoJ0FjY2VwdCcsIHJlcXVlc3QudHlwZXNbdHlwZV0gfHwgdHlwZSk7XG4gIHJldHVybiB0aGlzO1xufTtcblxuLyoqXG4gKiBTZXQgQXV0aG9yaXphdGlvbiBmaWVsZCB2YWx1ZSB3aXRoIGB1c2VyYCBhbmQgYHBhc3NgLlxuICpcbiAqIEBwYXJhbSB7U3RyaW5nfSB1c2VyXG4gKiBAcGFyYW0ge1N0cmluZ30gW3Bhc3NdIG9wdGlvbmFsIGluIGNhc2Ugb2YgdXNpbmcgJ2JlYXJlcicgYXMgdHlwZVxuICogQHBhcmFtIHtPYmplY3R9IG9wdGlvbnMgd2l0aCAndHlwZScgcHJvcGVydHkgJ2F1dG8nLCAnYmFzaWMnIG9yICdiZWFyZXInIChkZWZhdWx0ICdiYXNpYycpXG4gKiBAcmV0dXJuIHtSZXF1ZXN0fSBmb3IgY2hhaW5pbmdcbiAqIEBhcGkgcHVibGljXG4gKi9cblxuUmVxdWVzdC5wcm90b3R5cGUuYXV0aCA9IGZ1bmN0aW9uICh1c2VyLCBwYXNzLCBvcHRpb25zKSB7XG4gIGlmIChhcmd1bWVudHMubGVuZ3RoID09PSAxKSBwYXNzID0gJyc7XG4gIGlmICh0eXBlb2YgcGFzcyA9PT0gJ29iamVjdCcgJiYgcGFzcyAhPT0gbnVsbCkge1xuICAgIC8vIHBhc3MgaXMgb3B0aW9uYWwgYW5kIGNhbiBiZSByZXBsYWNlZCB3aXRoIG9wdGlvbnNcbiAgICBvcHRpb25zID0gcGFzcztcbiAgICBwYXNzID0gJyc7XG4gIH1cblxuICBpZiAoIW9wdGlvbnMpIHtcbiAgICBvcHRpb25zID0ge1xuICAgICAgdHlwZTogdHlwZW9mIGJ0b2EgPT09ICdmdW5jdGlvbicgPyAnYmFzaWMnIDogJ2F1dG8nXG4gICAgfTtcbiAgfVxuXG4gIGNvbnN0IGVuY29kZXIgPSBvcHRpb25zLmVuY29kZXJcbiAgICA/IG9wdGlvbnMuZW5jb2RlclxuICAgIDogKHN0cmluZykgPT4ge1xuICAgICAgICBpZiAodHlwZW9mIGJ0b2EgPT09ICdmdW5jdGlvbicpIHtcbiAgICAgICAgICByZXR1cm4gYnRvYShzdHJpbmcpO1xuICAgICAgICB9XG5cbiAgICAgICAgdGhyb3cgbmV3IEVycm9yKCdDYW5ub3QgdXNlIGJhc2ljIGF1dGgsIGJ0b2EgaXMgbm90IGEgZnVuY3Rpb24nKTtcbiAgICAgIH07XG5cbiAgcmV0dXJuIHRoaXMuX2F1dGgodXNlciwgcGFzcywgb3B0aW9ucywgZW5jb2Rlcik7XG59O1xuXG4vKipcbiAqIEFkZCBxdWVyeS1zdHJpbmcgYHZhbGAuXG4gKlxuICogRXhhbXBsZXM6XG4gKlxuICogICByZXF1ZXN0LmdldCgnL3Nob2VzJylcbiAqICAgICAucXVlcnkoJ3NpemU9MTAnKVxuICogICAgIC5xdWVyeSh7IGNvbG9yOiAnYmx1ZScgfSlcbiAqXG4gKiBAcGFyYW0ge09iamVjdHxTdHJpbmd9IHZhbFxuICogQHJldHVybiB7UmVxdWVzdH0gZm9yIGNoYWluaW5nXG4gKiBAYXBpIHB1YmxpY1xuICovXG5cblJlcXVlc3QucHJvdG90eXBlLnF1ZXJ5ID0gZnVuY3Rpb24gKHZhbHVlKSB7XG4gIGlmICh0eXBlb2YgdmFsdWUgIT09ICdzdHJpbmcnKSB2YWx1ZSA9IHNlcmlhbGl6ZSh2YWx1ZSk7XG4gIGlmICh2YWx1ZSkgdGhpcy5fcXVlcnkucHVzaCh2YWx1ZSk7XG4gIHJldHVybiB0aGlzO1xufTtcblxuLyoqXG4gKiBRdWV1ZSB0aGUgZ2l2ZW4gYGZpbGVgIGFzIGFuIGF0dGFjaG1lbnQgdG8gdGhlIHNwZWNpZmllZCBgZmllbGRgLFxuICogd2l0aCBvcHRpb25hbCBgb3B0aW9uc2AgKG9yIGZpbGVuYW1lKS5cbiAqXG4gKiBgYGAganNcbiAqIHJlcXVlc3QucG9zdCgnL3VwbG9hZCcpXG4gKiAgIC5hdHRhY2goJ2NvbnRlbnQnLCBuZXcgQmxvYihbJzxhIGlkPVwiYVwiPjxiIGlkPVwiYlwiPmhleSE8L2I+PC9hPiddLCB7IHR5cGU6IFwidGV4dC9odG1sXCJ9KSlcbiAqICAgLmVuZChjYWxsYmFjayk7XG4gKiBgYGBcbiAqXG4gKiBAcGFyYW0ge1N0cmluZ30gZmllbGRcbiAqIEBwYXJhbSB7QmxvYnxGaWxlfSBmaWxlXG4gKiBAcGFyYW0ge1N0cmluZ3xPYmplY3R9IG9wdGlvbnNcbiAqIEByZXR1cm4ge1JlcXVlc3R9IGZvciBjaGFpbmluZ1xuICogQGFwaSBwdWJsaWNcbiAqL1xuXG5SZXF1ZXN0LnByb3RvdHlwZS5hdHRhY2ggPSBmdW5jdGlvbiAoZmllbGQsIGZpbGUsIG9wdGlvbnMpIHtcbiAgaWYgKGZpbGUpIHtcbiAgICBpZiAodGhpcy5fZGF0YSkge1xuICAgICAgdGhyb3cgbmV3IEVycm9yKFwic3VwZXJhZ2VudCBjYW4ndCBtaXggLnNlbmQoKSBhbmQgLmF0dGFjaCgpXCIpO1xuICAgIH1cblxuICAgIHRoaXMuX2dldEZvcm1EYXRhKCkuYXBwZW5kKGZpZWxkLCBmaWxlLCBvcHRpb25zIHx8IGZpbGUubmFtZSk7XG4gIH1cblxuICByZXR1cm4gdGhpcztcbn07XG5cblJlcXVlc3QucHJvdG90eXBlLl9nZXRGb3JtRGF0YSA9IGZ1bmN0aW9uICgpIHtcbiAgaWYgKCF0aGlzLl9mb3JtRGF0YSkge1xuICAgIHRoaXMuX2Zvcm1EYXRhID0gbmV3IHJvb3QuRm9ybURhdGEoKTtcbiAgfVxuXG4gIHJldHVybiB0aGlzLl9mb3JtRGF0YTtcbn07XG5cbi8qKlxuICogSW52b2tlIHRoZSBjYWxsYmFjayB3aXRoIGBlcnJgIGFuZCBgcmVzYFxuICogYW5kIGhhbmRsZSBhcml0eSBjaGVjay5cbiAqXG4gKiBAcGFyYW0ge0Vycm9yfSBlcnJcbiAqIEBwYXJhbSB7UmVzcG9uc2V9IHJlc1xuICogQGFwaSBwcml2YXRlXG4gKi9cblxuUmVxdWVzdC5wcm90b3R5cGUuY2FsbGJhY2sgPSBmdW5jdGlvbiAoZXJyb3IsIHJlcykge1xuICBpZiAodGhpcy5fc2hvdWxkUmV0cnkoZXJyb3IsIHJlcykpIHtcbiAgICByZXR1cm4gdGhpcy5fcmV0cnkoKTtcbiAgfVxuXG4gIGNvbnN0IGZuID0gdGhpcy5fY2FsbGJhY2s7XG4gIHRoaXMuY2xlYXJUaW1lb3V0KCk7XG5cbiAgaWYgKGVycm9yKSB7XG4gICAgaWYgKHRoaXMuX21heFJldHJpZXMpIGVycm9yLnJldHJpZXMgPSB0aGlzLl9yZXRyaWVzIC0gMTtcbiAgICB0aGlzLmVtaXQoJ2Vycm9yJywgZXJyb3IpO1xuICB9XG5cbiAgZm4oZXJyb3IsIHJlcyk7XG59O1xuXG4vKipcbiAqIEludm9rZSBjYWxsYmFjayB3aXRoIHgtZG9tYWluIGVycm9yLlxuICpcbiAqIEBhcGkgcHJpdmF0ZVxuICovXG5cblJlcXVlc3QucHJvdG90eXBlLmNyb3NzRG9tYWluRXJyb3IgPSBmdW5jdGlvbiAoKSB7XG4gIGNvbnN0IGVycm9yID0gbmV3IEVycm9yKFxuICAgICdSZXF1ZXN0IGhhcyBiZWVuIHRlcm1pbmF0ZWRcXG5Qb3NzaWJsZSBjYXVzZXM6IHRoZSBuZXR3b3JrIGlzIG9mZmxpbmUsIE9yaWdpbiBpcyBub3QgYWxsb3dlZCBieSBBY2Nlc3MtQ29udHJvbC1BbGxvdy1PcmlnaW4sIHRoZSBwYWdlIGlzIGJlaW5nIHVubG9hZGVkLCBldGMuJ1xuICApO1xuICBlcnJvci5jcm9zc0RvbWFpbiA9IHRydWU7XG5cbiAgZXJyb3Iuc3RhdHVzID0gdGhpcy5zdGF0dXM7XG4gIGVycm9yLm1ldGhvZCA9IHRoaXMubWV0aG9kO1xuICBlcnJvci51cmwgPSB0aGlzLnVybDtcblxuICB0aGlzLmNhbGxiYWNrKGVycm9yKTtcbn07XG5cbi8vIFRoaXMgb25seSB3YXJucywgYmVjYXVzZSB0aGUgcmVxdWVzdCBpcyBzdGlsbCBsaWtlbHkgdG8gd29ya1xuUmVxdWVzdC5wcm90b3R5cGUuYWdlbnQgPSBmdW5jdGlvbiAoKSB7XG4gIGNvbnNvbGUud2FybignVGhpcyBpcyBub3Qgc3VwcG9ydGVkIGluIGJyb3dzZXIgdmVyc2lvbiBvZiBzdXBlcmFnZW50Jyk7XG4gIHJldHVybiB0aGlzO1xufTtcblxuUmVxdWVzdC5wcm90b3R5cGUuY2EgPSBSZXF1ZXN0LnByb3RvdHlwZS5hZ2VudDtcblJlcXVlc3QucHJvdG90eXBlLmJ1ZmZlciA9IFJlcXVlc3QucHJvdG90eXBlLmNhO1xuXG4vLyBUaGlzIHRocm93cywgYmVjYXVzZSBpdCBjYW4ndCBzZW5kL3JlY2VpdmUgZGF0YSBhcyBleHBlY3RlZFxuUmVxdWVzdC5wcm90b3R5cGUud3JpdGUgPSAoKSA9PiB7XG4gIHRocm93IG5ldyBFcnJvcihcbiAgICAnU3RyZWFtaW5nIGlzIG5vdCBzdXBwb3J0ZWQgaW4gYnJvd3NlciB2ZXJzaW9uIG9mIHN1cGVyYWdlbnQnXG4gICk7XG59O1xuXG5SZXF1ZXN0LnByb3RvdHlwZS5waXBlID0gUmVxdWVzdC5wcm90b3R5cGUud3JpdGU7XG5cbi8qKlxuICogQ2hlY2sgaWYgYG9iamAgaXMgYSBob3N0IG9iamVjdCxcbiAqIHdlIGRvbid0IHdhbnQgdG8gc2VyaWFsaXplIHRoZXNlIDopXG4gKlxuICogQHBhcmFtIHtPYmplY3R9IG9iaiBob3N0IG9iamVjdFxuICogQHJldHVybiB7Qm9vbGVhbn0gaXMgYSBob3N0IG9iamVjdFxuICogQGFwaSBwcml2YXRlXG4gKi9cblJlcXVlc3QucHJvdG90eXBlLl9pc0hvc3QgPSBmdW5jdGlvbiAob2JqZWN0KSB7XG4gIC8vIE5hdGl2ZSBvYmplY3RzIHN0cmluZ2lmeSB0byBbb2JqZWN0IEZpbGVdLCBbb2JqZWN0IEJsb2JdLCBbb2JqZWN0IEZvcm1EYXRhXSwgZXRjLlxuICByZXR1cm4gKFxuICAgIG9iamVjdCAmJlxuICAgIHR5cGVvZiBvYmplY3QgPT09ICdvYmplY3QnICYmXG4gICAgIUFycmF5LmlzQXJyYXkob2JqZWN0KSAmJlxuICAgIE9iamVjdC5wcm90b3R5cGUudG9TdHJpbmcuY2FsbChvYmplY3QpICE9PSAnW29iamVjdCBPYmplY3RdJ1xuICApO1xufTtcblxuLyoqXG4gKiBJbml0aWF0ZSByZXF1ZXN0LCBpbnZva2luZyBjYWxsYmFjayBgZm4ocmVzKWBcbiAqIHdpdGggYW4gaW5zdGFuY2VvZiBgUmVzcG9uc2VgLlxuICpcbiAqIEBwYXJhbSB7RnVuY3Rpb259IGZuXG4gKiBAcmV0dXJuIHtSZXF1ZXN0fSBmb3IgY2hhaW5pbmdcbiAqIEBhcGkgcHVibGljXG4gKi9cblxuUmVxdWVzdC5wcm90b3R5cGUuZW5kID0gZnVuY3Rpb24gKGZuKSB7XG4gIGlmICh0aGlzLl9lbmRDYWxsZWQpIHtcbiAgICBjb25zb2xlLndhcm4oXG4gICAgICAnV2FybmluZzogLmVuZCgpIHdhcyBjYWxsZWQgdHdpY2UuIFRoaXMgaXMgbm90IHN1cHBvcnRlZCBpbiBzdXBlcmFnZW50J1xuICAgICk7XG4gIH1cblxuICB0aGlzLl9lbmRDYWxsZWQgPSB0cnVlO1xuXG4gIC8vIHN0b3JlIGNhbGxiYWNrXG4gIHRoaXMuX2NhbGxiYWNrID0gZm4gfHwgbm9vcDtcblxuICAvLyBxdWVyeXN0cmluZ1xuICB0aGlzLl9maW5hbGl6ZVF1ZXJ5U3RyaW5nKCk7XG5cbiAgdGhpcy5fZW5kKCk7XG59O1xuXG5SZXF1ZXN0LnByb3RvdHlwZS5fc2V0VXBsb2FkVGltZW91dCA9IGZ1bmN0aW9uICgpIHtcbiAgY29uc3Qgc2VsZiA9IHRoaXM7XG5cbiAgLy8gdXBsb2FkIHRpbWVvdXQgaXQncyB3b2tycyBvbmx5IGlmIGRlYWRsaW5lIHRpbWVvdXQgaXMgb2ZmXG4gIGlmICh0aGlzLl91cGxvYWRUaW1lb3V0ICYmICF0aGlzLl91cGxvYWRUaW1lb3V0VGltZXIpIHtcbiAgICB0aGlzLl91cGxvYWRUaW1lb3V0VGltZXIgPSBzZXRUaW1lb3V0KCgpID0+IHtcbiAgICAgIHNlbGYuX3RpbWVvdXRFcnJvcihcbiAgICAgICAgJ1VwbG9hZCB0aW1lb3V0IG9mICcsXG4gICAgICAgIHNlbGYuX3VwbG9hZFRpbWVvdXQsXG4gICAgICAgICdFVElNRURPVVQnXG4gICAgICApO1xuICAgIH0sIHRoaXMuX3VwbG9hZFRpbWVvdXQpO1xuICB9XG59O1xuXG4vLyBlc2xpbnQtZGlzYWJsZS1uZXh0LWxpbmUgY29tcGxleGl0eVxuUmVxdWVzdC5wcm90b3R5cGUuX2VuZCA9IGZ1bmN0aW9uICgpIHtcbiAgaWYgKHRoaXMuX2Fib3J0ZWQpXG4gICAgcmV0dXJuIHRoaXMuY2FsbGJhY2soXG4gICAgICBuZXcgRXJyb3IoJ1RoZSByZXF1ZXN0IGhhcyBiZWVuIGFib3J0ZWQgZXZlbiBiZWZvcmUgLmVuZCgpIHdhcyBjYWxsZWQnKVxuICAgICk7XG5cbiAgY29uc3Qgc2VsZiA9IHRoaXM7XG4gIHRoaXMueGhyID0gcmVxdWVzdC5nZXRYSFIoKTtcbiAgY29uc3QgeyB4aHIgfSA9IHRoaXM7XG4gIGxldCBkYXRhID0gdGhpcy5fZm9ybURhdGEgfHwgdGhpcy5fZGF0YTtcblxuICB0aGlzLl9zZXRUaW1lb3V0cygpO1xuXG4gIC8vIHN0YXRlIGNoYW5nZVxuICB4aHIuYWRkRXZlbnRMaXN0ZW5lcigncmVhZHlzdGF0ZWNoYW5nZScsICgpID0+IHtcbiAgICBjb25zdCB7IHJlYWR5U3RhdGUgfSA9IHhocjtcbiAgICBpZiAocmVhZHlTdGF0ZSA+PSAyICYmIHNlbGYuX3Jlc3BvbnNlVGltZW91dFRpbWVyKSB7XG4gICAgICBjbGVhclRpbWVvdXQoc2VsZi5fcmVzcG9uc2VUaW1lb3V0VGltZXIpO1xuICAgIH1cblxuICAgIGlmIChyZWFkeVN0YXRlICE9PSA0KSB7XG4gICAgICByZXR1cm47XG4gICAgfVxuXG4gICAgLy8gSW4gSUU5LCByZWFkcyB0byBhbnkgcHJvcGVydHkgKGUuZy4gc3RhdHVzKSBvZmYgb2YgYW4gYWJvcnRlZCBYSFIgd2lsbFxuICAgIC8vIHJlc3VsdCBpbiB0aGUgZXJyb3IgXCJDb3VsZCBub3QgY29tcGxldGUgdGhlIG9wZXJhdGlvbiBkdWUgdG8gZXJyb3IgYzAwYzAyM2ZcIlxuICAgIGxldCBzdGF0dXM7XG4gICAgdHJ5IHtcbiAgICAgIHN0YXR1cyA9IHhoci5zdGF0dXM7XG4gICAgfSBjYXRjaCB7XG4gICAgICBzdGF0dXMgPSAwO1xuICAgIH1cblxuICAgIGlmICghc3RhdHVzKSB7XG4gICAgICBpZiAoc2VsZi50aW1lZG91dCB8fCBzZWxmLl9hYm9ydGVkKSByZXR1cm47XG4gICAgICByZXR1cm4gc2VsZi5jcm9zc0RvbWFpbkVycm9yKCk7XG4gICAgfVxuXG4gICAgc2VsZi5lbWl0KCdlbmQnKTtcbiAgfSk7XG5cbiAgLy8gcHJvZ3Jlc3NcbiAgY29uc3QgaGFuZGxlUHJvZ3Jlc3MgPSAoZGlyZWN0aW9uLCBlKSA9PiB7XG4gICAgaWYgKGUudG90YWwgPiAwKSB7XG4gICAgICBlLnBlcmNlbnQgPSAoZS5sb2FkZWQgLyBlLnRvdGFsKSAqIDEwMDtcblxuICAgICAgaWYgKGUucGVyY2VudCA9PT0gMTAwKSB7XG4gICAgICAgIGNsZWFyVGltZW91dChzZWxmLl91cGxvYWRUaW1lb3V0VGltZXIpO1xuICAgICAgfVxuICAgIH1cblxuICAgIGUuZGlyZWN0aW9uID0gZGlyZWN0aW9uO1xuICAgIHNlbGYuZW1pdCgncHJvZ3Jlc3MnLCBlKTtcbiAgfTtcblxuICBpZiAodGhpcy5oYXNMaXN0ZW5lcnMoJ3Byb2dyZXNzJykpIHtcbiAgICB0cnkge1xuICAgICAgeGhyLmFkZEV2ZW50TGlzdGVuZXIoJ3Byb2dyZXNzJywgaGFuZGxlUHJvZ3Jlc3MuYmluZChudWxsLCAnZG93bmxvYWQnKSk7XG4gICAgICBpZiAoeGhyLnVwbG9hZCkge1xuICAgICAgICB4aHIudXBsb2FkLmFkZEV2ZW50TGlzdGVuZXIoXG4gICAgICAgICAgJ3Byb2dyZXNzJyxcbiAgICAgICAgICBoYW5kbGVQcm9ncmVzcy5iaW5kKG51bGwsICd1cGxvYWQnKVxuICAgICAgICApO1xuICAgICAgfVxuICAgIH0gY2F0Y2gge1xuICAgICAgLy8gQWNjZXNzaW5nIHhoci51cGxvYWQgZmFpbHMgaW4gSUUgZnJvbSBhIHdlYiB3b3JrZXIsIHNvIGp1c3QgcHJldGVuZCBpdCBkb2Vzbid0IGV4aXN0LlxuICAgICAgLy8gUmVwb3J0ZWQgaGVyZTpcbiAgICAgIC8vIGh0dHBzOi8vY29ubmVjdC5taWNyb3NvZnQuY29tL0lFL2ZlZWRiYWNrL2RldGFpbHMvODM3MjQ1L3htbGh0dHByZXF1ZXN0LXVwbG9hZC10aHJvd3MtaW52YWxpZC1hcmd1bWVudC13aGVuLXVzZWQtZnJvbS13ZWItd29ya2VyLWNvbnRleHRcbiAgICB9XG4gIH1cblxuICBpZiAoeGhyLnVwbG9hZCkge1xuICAgIHRoaXMuX3NldFVwbG9hZFRpbWVvdXQoKTtcbiAgfVxuXG4gIC8vIGluaXRpYXRlIHJlcXVlc3RcbiAgdHJ5IHtcbiAgICBpZiAodGhpcy51c2VybmFtZSAmJiB0aGlzLnBhc3N3b3JkKSB7XG4gICAgICB4aHIub3Blbih0aGlzLm1ldGhvZCwgdGhpcy51cmwsIHRydWUsIHRoaXMudXNlcm5hbWUsIHRoaXMucGFzc3dvcmQpO1xuICAgIH0gZWxzZSB7XG4gICAgICB4aHIub3Blbih0aGlzLm1ldGhvZCwgdGhpcy51cmwsIHRydWUpO1xuICAgIH1cbiAgfSBjYXRjaCAoZXJyKSB7XG4gICAgLy8gc2VlICMxMTQ5XG4gICAgcmV0dXJuIHRoaXMuY2FsbGJhY2soZXJyKTtcbiAgfVxuXG4gIC8vIENPUlNcbiAgaWYgKHRoaXMuX3dpdGhDcmVkZW50aWFscykgeGhyLndpdGhDcmVkZW50aWFscyA9IHRydWU7XG5cbiAgLy8gYm9keVxuICBpZiAoXG4gICAgIXRoaXMuX2Zvcm1EYXRhICYmXG4gICAgdGhpcy5tZXRob2QgIT09ICdHRVQnICYmXG4gICAgdGhpcy5tZXRob2QgIT09ICdIRUFEJyAmJlxuICAgIHR5cGVvZiBkYXRhICE9PSAnc3RyaW5nJyAmJlxuICAgICF0aGlzLl9pc0hvc3QoZGF0YSlcbiAgKSB7XG4gICAgLy8gc2VyaWFsaXplIHN0dWZmXG4gICAgY29uc3QgY29udGVudFR5cGUgPSB0aGlzLl9oZWFkZXJbJ2NvbnRlbnQtdHlwZSddO1xuICAgIGxldCBzZXJpYWxpemUgPVxuICAgICAgdGhpcy5fc2VyaWFsaXplciB8fFxuICAgICAgcmVxdWVzdC5zZXJpYWxpemVbY29udGVudFR5cGUgPyBjb250ZW50VHlwZS5zcGxpdCgnOycpWzBdIDogJyddO1xuICAgIGlmICghc2VyaWFsaXplICYmIGlzSlNPTihjb250ZW50VHlwZSkpIHtcbiAgICAgIHNlcmlhbGl6ZSA9IHJlcXVlc3Quc2VyaWFsaXplWydhcHBsaWNhdGlvbi9qc29uJ107XG4gICAgfVxuXG4gICAgaWYgKHNlcmlhbGl6ZSkgZGF0YSA9IHNlcmlhbGl6ZShkYXRhKTtcbiAgfVxuXG4gIC8vIHNldCBoZWFkZXIgZmllbGRzXG4gIGZvciAoY29uc3QgZmllbGQgaW4gdGhpcy5oZWFkZXIpIHtcbiAgICBpZiAodGhpcy5oZWFkZXJbZmllbGRdID09PSBudWxsKSBjb250aW51ZTtcblxuICAgIGlmIChoYXNPd24odGhpcy5oZWFkZXIsIGZpZWxkKSlcbiAgICAgIHhoci5zZXRSZXF1ZXN0SGVhZGVyKGZpZWxkLCB0aGlzLmhlYWRlcltmaWVsZF0pO1xuICB9XG5cbiAgaWYgKHRoaXMuX3Jlc3BvbnNlVHlwZSkge1xuICAgIHhoci5yZXNwb25zZVR5cGUgPSB0aGlzLl9yZXNwb25zZVR5cGU7XG4gIH1cblxuICAvLyBzZW5kIHN0dWZmXG4gIHRoaXMuZW1pdCgncmVxdWVzdCcsIHRoaXMpO1xuXG4gIC8vIElFMTEgeGhyLnNlbmQodW5kZWZpbmVkKSBzZW5kcyAndW5kZWZpbmVkJyBzdHJpbmcgYXMgUE9TVCBwYXlsb2FkIChpbnN0ZWFkIG9mIG5vdGhpbmcpXG4gIC8vIFdlIG5lZWQgbnVsbCBoZXJlIGlmIGRhdGEgaXMgdW5kZWZpbmVkXG4gIHhoci5zZW5kKHR5cGVvZiBkYXRhID09PSAndW5kZWZpbmVkJyA/IG51bGwgOiBkYXRhKTtcbn07XG5cbnJlcXVlc3QuYWdlbnQgPSAoKSA9PiBuZXcgQWdlbnQoKTtcblxuZm9yIChjb25zdCBtZXRob2Qgb2YgWydHRVQnLCAnUE9TVCcsICdPUFRJT05TJywgJ1BBVENIJywgJ1BVVCcsICdERUxFVEUnXSkge1xuICBBZ2VudC5wcm90b3R5cGVbbWV0aG9kLnRvTG93ZXJDYXNlKCldID0gZnVuY3Rpb24gKHVybCwgZm4pIHtcbiAgICBjb25zdCByZXF1ZXN0XyA9IG5ldyByZXF1ZXN0LlJlcXVlc3QobWV0aG9kLCB1cmwpO1xuICAgIHRoaXMuX3NldERlZmF1bHRzKHJlcXVlc3RfKTtcbiAgICBpZiAoZm4pIHtcbiAgICAgIHJlcXVlc3RfLmVuZChmbik7XG4gICAgfVxuXG4gICAgcmV0dXJuIHJlcXVlc3RfO1xuICB9O1xufVxuXG5BZ2VudC5wcm90b3R5cGUuZGVsID0gQWdlbnQucHJvdG90eXBlLmRlbGV0ZTtcblxuLyoqXG4gKiBHRVQgYHVybGAgd2l0aCBvcHRpb25hbCBjYWxsYmFjayBgZm4ocmVzKWAuXG4gKlxuICogQHBhcmFtIHtTdHJpbmd9IHVybFxuICogQHBhcmFtIHtNaXhlZHxGdW5jdGlvbn0gW2RhdGFdIG9yIGZuXG4gKiBAcGFyYW0ge0Z1bmN0aW9ufSBbZm5dXG4gKiBAcmV0dXJuIHtSZXF1ZXN0fVxuICogQGFwaSBwdWJsaWNcbiAqL1xuXG5yZXF1ZXN0LmdldCA9ICh1cmwsIGRhdGEsIGZuKSA9PiB7XG4gIGNvbnN0IHJlcXVlc3RfID0gcmVxdWVzdCgnR0VUJywgdXJsKTtcbiAgaWYgKHR5cGVvZiBkYXRhID09PSAnZnVuY3Rpb24nKSB7XG4gICAgZm4gPSBkYXRhO1xuICAgIGRhdGEgPSBudWxsO1xuICB9XG5cbiAgaWYgKGRhdGEpIHJlcXVlc3RfLnF1ZXJ5KGRhdGEpO1xuICBpZiAoZm4pIHJlcXVlc3RfLmVuZChmbik7XG4gIHJldHVybiByZXF1ZXN0Xztcbn07XG5cbi8qKlxuICogSEVBRCBgdXJsYCB3aXRoIG9wdGlvbmFsIGNhbGxiYWNrIGBmbihyZXMpYC5cbiAqXG4gKiBAcGFyYW0ge1N0cmluZ30gdXJsXG4gKiBAcGFyYW0ge01peGVkfEZ1bmN0aW9ufSBbZGF0YV0gb3IgZm5cbiAqIEBwYXJhbSB7RnVuY3Rpb259IFtmbl1cbiAqIEByZXR1cm4ge1JlcXVlc3R9XG4gKiBAYXBpIHB1YmxpY1xuICovXG5cbnJlcXVlc3QuaGVhZCA9ICh1cmwsIGRhdGEsIGZuKSA9PiB7XG4gIGNvbnN0IHJlcXVlc3RfID0gcmVxdWVzdCgnSEVBRCcsIHVybCk7XG4gIGlmICh0eXBlb2YgZGF0YSA9PT0gJ2Z1bmN0aW9uJykge1xuICAgIGZuID0gZGF0YTtcbiAgICBkYXRhID0gbnVsbDtcbiAgfVxuXG4gIGlmIChkYXRhKSByZXF1ZXN0Xy5xdWVyeShkYXRhKTtcbiAgaWYgKGZuKSByZXF1ZXN0Xy5lbmQoZm4pO1xuICByZXR1cm4gcmVxdWVzdF87XG59O1xuXG4vKipcbiAqIE9QVElPTlMgcXVlcnkgdG8gYHVybGAgd2l0aCBvcHRpb25hbCBjYWxsYmFjayBgZm4ocmVzKWAuXG4gKlxuICogQHBhcmFtIHtTdHJpbmd9IHVybFxuICogQHBhcmFtIHtNaXhlZHxGdW5jdGlvbn0gW2RhdGFdIG9yIGZuXG4gKiBAcGFyYW0ge0Z1bmN0aW9ufSBbZm5dXG4gKiBAcmV0dXJuIHtSZXF1ZXN0fVxuICogQGFwaSBwdWJsaWNcbiAqL1xuXG5yZXF1ZXN0Lm9wdGlvbnMgPSAodXJsLCBkYXRhLCBmbikgPT4ge1xuICBjb25zdCByZXF1ZXN0XyA9IHJlcXVlc3QoJ09QVElPTlMnLCB1cmwpO1xuICBpZiAodHlwZW9mIGRhdGEgPT09ICdmdW5jdGlvbicpIHtcbiAgICBmbiA9IGRhdGE7XG4gICAgZGF0YSA9IG51bGw7XG4gIH1cblxuICBpZiAoZGF0YSkgcmVxdWVzdF8uc2VuZChkYXRhKTtcbiAgaWYgKGZuKSByZXF1ZXN0Xy5lbmQoZm4pO1xuICByZXR1cm4gcmVxdWVzdF87XG59O1xuXG4vKipcbiAqIERFTEVURSBgdXJsYCB3aXRoIG9wdGlvbmFsIGBkYXRhYCBhbmQgY2FsbGJhY2sgYGZuKHJlcylgLlxuICpcbiAqIEBwYXJhbSB7U3RyaW5nfSB1cmxcbiAqIEBwYXJhbSB7TWl4ZWR9IFtkYXRhXVxuICogQHBhcmFtIHtGdW5jdGlvbn0gW2ZuXVxuICogQHJldHVybiB7UmVxdWVzdH1cbiAqIEBhcGkgcHVibGljXG4gKi9cblxuZnVuY3Rpb24gZGVsKHVybCwgZGF0YSwgZm4pIHtcbiAgY29uc3QgcmVxdWVzdF8gPSByZXF1ZXN0KCdERUxFVEUnLCB1cmwpO1xuICBpZiAodHlwZW9mIGRhdGEgPT09ICdmdW5jdGlvbicpIHtcbiAgICBmbiA9IGRhdGE7XG4gICAgZGF0YSA9IG51bGw7XG4gIH1cblxuICBpZiAoZGF0YSkgcmVxdWVzdF8uc2VuZChkYXRhKTtcbiAgaWYgKGZuKSByZXF1ZXN0Xy5lbmQoZm4pO1xuICByZXR1cm4gcmVxdWVzdF87XG59XG5cbnJlcXVlc3QuZGVsID0gZGVsO1xucmVxdWVzdC5kZWxldGUgPSBkZWw7XG5cbi8qKlxuICogUEFUQ0ggYHVybGAgd2l0aCBvcHRpb25hbCBgZGF0YWAgYW5kIGNhbGxiYWNrIGBmbihyZXMpYC5cbiAqXG4gKiBAcGFyYW0ge1N0cmluZ30gdXJsXG4gKiBAcGFyYW0ge01peGVkfSBbZGF0YV1cbiAqIEBwYXJhbSB7RnVuY3Rpb259IFtmbl1cbiAqIEByZXR1cm4ge1JlcXVlc3R9XG4gKiBAYXBpIHB1YmxpY1xuICovXG5cbnJlcXVlc3QucGF0Y2ggPSAodXJsLCBkYXRhLCBmbikgPT4ge1xuICBjb25zdCByZXF1ZXN0XyA9IHJlcXVlc3QoJ1BBVENIJywgdXJsKTtcbiAgaWYgKHR5cGVvZiBkYXRhID09PSAnZnVuY3Rpb24nKSB7XG4gICAgZm4gPSBkYXRhO1xuICAgIGRhdGEgPSBudWxsO1xuICB9XG5cbiAgaWYgKGRhdGEpIHJlcXVlc3RfLnNlbmQoZGF0YSk7XG4gIGlmIChmbikgcmVxdWVzdF8uZW5kKGZuKTtcbiAgcmV0dXJuIHJlcXVlc3RfO1xufTtcblxuLyoqXG4gKiBQT1NUIGB1cmxgIHdpdGggb3B0aW9uYWwgYGRhdGFgIGFuZCBjYWxsYmFjayBgZm4ocmVzKWAuXG4gKlxuICogQHBhcmFtIHtTdHJpbmd9IHVybFxuICogQHBhcmFtIHtNaXhlZH0gW2RhdGFdXG4gKiBAcGFyYW0ge0Z1bmN0aW9ufSBbZm5dXG4gKiBAcmV0dXJuIHtSZXF1ZXN0fVxuICogQGFwaSBwdWJsaWNcbiAqL1xuXG5yZXF1ZXN0LnBvc3QgPSAodXJsLCBkYXRhLCBmbikgPT4ge1xuICBjb25zdCByZXF1ZXN0XyA9IHJlcXVlc3QoJ1BPU1QnLCB1cmwpO1xuICBpZiAodHlwZW9mIGRhdGEgPT09ICdmdW5jdGlvbicpIHtcbiAgICBmbiA9IGRhdGE7XG4gICAgZGF0YSA9IG51bGw7XG4gIH1cblxuICBpZiAoZGF0YSkgcmVxdWVzdF8uc2VuZChkYXRhKTtcbiAgaWYgKGZuKSByZXF1ZXN0Xy5lbmQoZm4pO1xuICByZXR1cm4gcmVxdWVzdF87XG59O1xuXG4vKipcbiAqIFBVVCBgdXJsYCB3aXRoIG9wdGlvbmFsIGBkYXRhYCBhbmQgY2FsbGJhY2sgYGZuKHJlcylgLlxuICpcbiAqIEBwYXJhbSB7U3RyaW5nfSB1cmxcbiAqIEBwYXJhbSB7TWl4ZWR8RnVuY3Rpb259IFtkYXRhXSBvciBmblxuICogQHBhcmFtIHtGdW5jdGlvbn0gW2ZuXVxuICogQHJldHVybiB7UmVxdWVzdH1cbiAqIEBhcGkgcHVibGljXG4gKi9cblxucmVxdWVzdC5wdXQgPSAodXJsLCBkYXRhLCBmbikgPT4ge1xuICBjb25zdCByZXF1ZXN0XyA9IHJlcXVlc3QoJ1BVVCcsIHVybCk7XG4gIGlmICh0eXBlb2YgZGF0YSA9PT0gJ2Z1bmN0aW9uJykge1xuICAgIGZuID0gZGF0YTtcbiAgICBkYXRhID0gbnVsbDtcbiAgfVxuXG4gIGlmIChkYXRhKSByZXF1ZXN0Xy5zZW5kKGRhdGEpO1xuICBpZiAoZm4pIHJlcXVlc3RfLmVuZChmbik7XG4gIHJldHVybiByZXF1ZXN0Xztcbn07XG4iXSwibWFwcGluZ3MiOiI7Ozs7Ozs7Ozs7QUFBQTtBQUNBO0FBQ0E7QUFFQSxJQUFJQSxJQUFKOztBQUNBLElBQUksT0FBT0MsTUFBUCxLQUFrQixXQUF0QixFQUFtQztFQUNqQztFQUNBRCxJQUFJLEdBQUdDLE1BQVA7QUFDRCxDQUhELE1BR08sSUFBSSxPQUFPQyxJQUFQLEtBQWdCLFdBQXBCLEVBQWlDO0VBQ3RDO0VBQ0FDLE9BQU8sQ0FBQ0MsSUFBUixDQUNFLHFFQURGO0VBR0FKLElBQUksU0FBSjtBQUNELENBTk0sTUFNQTtFQUNMO0VBQ0FBLElBQUksR0FBR0UsSUFBUDtBQUNEOztBQUVELElBQU1HLE9BQU8sR0FBR0MsT0FBTyxDQUFDLG1CQUFELENBQXZCOztBQUNBLElBQU1DLGFBQWEsR0FBR0QsT0FBTyxDQUFDLHFCQUFELENBQTdCOztBQUNBLElBQU1FLEVBQUUsR0FBR0YsT0FBTyxDQUFDLElBQUQsQ0FBbEI7O0FBQ0EsSUFBTUcsV0FBVyxHQUFHSCxPQUFPLENBQUMsZ0JBQUQsQ0FBM0I7O0FBQ0EsZUFBb0NBLE9BQU8sQ0FBQyxTQUFELENBQTNDO0FBQUEsSUFBUUksUUFBUixZQUFRQSxRQUFSO0FBQUEsSUFBa0JDLEtBQWxCLFlBQWtCQSxLQUFsQjtBQUFBLElBQXlCQyxNQUF6QixZQUF5QkEsTUFBekI7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