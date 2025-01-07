"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.readdirpPromise = exports.readdirp = exports.ReaddirpStream = void 0;
const promises_1 = require("fs/promises");
const stream_1 = require("stream");
const path_1 = require("path");
function defaultOptions() {
    return {
        root: '.',
        fileFilter: (_path) => true,
        directoryFilter: (_path) => true,
        type: FILE_TYPE,
        lstat: false,
        depth: 2147483648,
        alwaysStat: false,
        highWaterMark: 4096,
    };
}
const RECURSIVE_ERROR_CODE = 'READDIRP_RECURSIVE_ERROR';
const NORMAL_FLOW_ERRORS = new Set(['ENOENT', 'EPERM', 'EACCES', 'ELOOP', RECURSIVE_ERROR_CODE]);
const FILE_TYPE = 'files';
const DIR_TYPE = 'directories';
const FILE_DIR_TYPE = 'files_directories';
const EVERYTHING_TYPE = 'all';
const ALL_TYPES = [FILE_TYPE, DIR_TYPE, FILE_DIR_TYPE, EVERYTHING_TYPE];
const DIR_TYPES = new Set([DIR_TYPE, FILE_DIR_TYPE, EVERYTHING_TYPE]);
const FILE_TYPES = new Set([FILE_TYPE, FILE_DIR_TYPE, EVERYTHING_TYPE]);
const isNormalFlowError = (error) => NORMAL_FLOW_ERRORS.has(error.code);
const wantBigintFsStats = process.platform === 'win32';
const emptyFn = (_path) => true;
const normalizeFilter = (filter) => {
    if (filter === undefined)
        return emptyFn;
    if (typeof filter === 'function')
        return filter;
    if (typeof filter === 'string') {
        const fl = filter.trim();
        return (entry) => entry.basename === fl;
    }
    if (Array.isArray(filter)) {
        const trItems = filter.map((item) => item.trim());
        return (entry) => trItems.some((f) => entry.basename === f);
    }
    return emptyFn;
};
class ReaddirpStream extends stream_1.Readable {
    constructor(options = {}) {
        super({
            objectMode: true,
            autoDestroy: true,
            highWaterMark: options.highWaterMark,
        });
        const opts = { ...defaultOptions(), ...options };
        const { root, type } = opts;
        this._fileFilter = normalizeFilter(opts.fileFilter);
        this._directoryFilter = normalizeFilter(opts.directoryFilter);
        const statMethod = opts.lstat ? promises_1.lstat : promises_1.stat;
        // Use bigint stats if it's windows and stat() supports options (node 10+).
        if (wantBigintFsStats) {
            this._stat = (path) => statMethod(path, { bigint: true });
        }
        else {
            this._stat = statMethod;
        }
        this._maxDepth = opts.depth;
        this._wantsDir = DIR_TYPES.has(type);
        this._wantsFile = FILE_TYPES.has(type);
        this._wantsEverything = type === EVERYTHING_TYPE;
        this._root = (0, path_1.resolve)(root);
        this._isDirent = !opts.alwaysStat;
        this._statsProp = this._isDirent ? 'dirent' : 'stats';
        this._rdOptions = { encoding: 'utf8', withFileTypes: this._isDirent };
        // Launch stream with one parent, the root dir.
        this.parents = [this._exploreDir(root, 1)];
        this.reading = false;
        this.parent = undefined;
    }
    async _read(batch) {
        if (this.reading)
            return;
        this.reading = true;
        try {
            while (!this.destroyed && batch > 0) {
                const par = this.parent;
                const fil = par && par.files;
                if (fil && fil.length > 0) {
                    const { path, depth } = par;
                    const slice = fil.splice(0, batch).map((dirent) => this._formatEntry(dirent, path));
                    const awaited = await Promise.all(slice);
                    for (const entry of awaited) {
                        if (!entry) {
                            batch--;
                            return;
                        }
                        if (this.destroyed)
                            return;
                        const entryType = await this._getEntryType(entry);
                        if (entryType === 'directory' && this._directoryFilter(entry)) {
                            if (depth <= this._maxDepth) {
                                this.parents.push(this._exploreDir(entry.fullPath, depth + 1));
                            }
                            if (this._wantsDir) {
                                this.push(entry);
                                batch--;
                            }
                        }
                        else if ((entryType === 'file' || this._includeAsFile(entry)) &&
                            this._fileFilter(entry)) {
                            if (this._wantsFile) {
                                this.push(entry);
                                batch--;
                            }
                        }
                    }
                }
                else {
                    const parent = this.parents.pop();
                    if (!parent) {
                        this.push(null);
                        break;
                    }
                    this.parent = await parent;
                    if (this.destroyed)
                        return;
                }
            }
        }
        catch (error) {
            this.destroy(error);
        }
        finally {
            this.reading = false;
        }
    }
    async _exploreDir(path, depth) {
        let files;
        try {
            files = await (0, promises_1.readdir)(path, this._rdOptions);
        }
        catch (error) {
            this._onError(error);
        }
        return { files, depth, path };
    }
    async _formatEntry(dirent, path) {
        let entry;
        const basename = this._isDirent ? dirent.name : dirent;
        try {
            const fullPath = (0, path_1.resolve)((0, path_1.join)(path, basename));
            entry = { path: (0, path_1.relative)(this._root, fullPath), fullPath, basename };
            entry[this._statsProp] = this._isDirent ? dirent : await this._stat(fullPath);
        }
        catch (err) {
            this._onError(err);
            return;
        }
        return entry;
    }
    _onError(err) {
        if (isNormalFlowError(err) && !this.destroyed) {
            this.emit('warn', err);
        }
        else {
            this.destroy(err);
        }
    }
    async _getEntryType(entry) {
        // entry may be undefined, because a warning or an error were emitted
        // and the statsProp is undefined
        if (!entry && this._statsProp in entry) {
            return '';
        }
        const stats = entry[this._statsProp];
        if (stats.isFile())
            return 'file';
        if (stats.isDirectory())
            return 'directory';
        if (stats && stats.isSymbolicLink()) {
            const full = entry.fullPath;
            try {
                const entryRealPath = await (0, promises_1.realpath)(full);
                const entryRealPathStats = await (0, promises_1.lstat)(entryRealPath);
                if (entryRealPathStats.isFile()) {
                    return 'file';
                }
                if (entryRealPathStats.isDirectory()) {
                    const len = entryRealPath.length;
                    if (full.startsWith(entryRealPath) && full.substr(len, 1) === path_1.sep) {
                        const recursiveError = new Error(`Circular symlink detected: "${full}" points to "${entryRealPath}"`);
                        // @ts-ignore
                        recursiveError.code = RECURSIVE_ERROR_CODE;
                        return this._onError(recursiveError);
                    }
                    return 'directory';
                }
            }
            catch (error) {
                this._onError(error);
                return '';
            }
        }
    }
    _includeAsFile(entry) {
        const stats = entry && entry[this._statsProp];
        return stats && this._wantsEverything && !stats.isDirectory();
    }
}
exports.ReaddirpStream = ReaddirpStream;
/**
 * Main function which ends up calling readdirRec and reads all files and directories in given root recursively.
 * @param root Root directory
 * @param options Options to specify root (start directory), filters and recursion depth
 */
const readdirp = (root, options = {}) => {
    // @ts-ignore
    let type = options.entryType || options.type;
    if (type === 'both')
        type = FILE_DIR_TYPE; // backwards-compatibility
    if (type)
        options.type = type;
    if (!root) {
        throw new Error('readdirp: root argument is required. Usage: readdirp(root, options)');
    }
    else if (typeof root !== 'string') {
        throw new TypeError('readdirp: root argument must be a string. Usage: readdirp(root, options)');
    }
    else if (type && !ALL_TYPES.includes(type)) {
        throw new Error(`readdirp: Invalid type passed. Use one of ${ALL_TYPES.join(', ')}`);
    }
    options.root = root;
    return new ReaddirpStream(options);
};
exports.readdirp = readdirp;
const readdirpPromise = (root, options = {}) => {
    return new Promise((resolve, reject) => {
        const files = [];
        (0, exports.readdirp)(root, options)
            .on('data', (entry) => files.push(entry))
            .on('end', () => resolve(files))
            .on('error', (error) => reject(error));
    });
};
exports.readdirpPromise = readdirpPromise;
exports.default = exports.readdirp;
