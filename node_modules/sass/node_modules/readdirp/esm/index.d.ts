import type { Stats, Dirent } from 'fs';
import { Readable } from 'stream';
export type Path = string;
export interface EntryInfo {
    path: string;
    fullPath: string;
    stats?: Stats;
    dirent?: Dirent;
    basename: string;
}
export type PathOrDirent = Dirent | Path;
export type Tester = (path: EntryInfo) => boolean;
export type Predicate = string[] | string | Tester;
declare function defaultOptions(): {
    root: string;
    fileFilter: (_path: EntryInfo) => boolean;
    directoryFilter: (_path: EntryInfo) => boolean;
    type: string;
    lstat: boolean;
    depth: number;
    alwaysStat: boolean;
    highWaterMark: number;
};
export type ReaddirpOptions = ReturnType<typeof defaultOptions>;
export interface DirEntry {
    files: PathOrDirent[];
    depth: number;
    path: Path;
}
export declare class ReaddirpStream extends Readable {
    parents: any[];
    reading: boolean;
    parent?: DirEntry;
    _stat: Function;
    _maxDepth: number;
    _wantsDir: boolean;
    _wantsFile: boolean;
    _wantsEverything: boolean;
    _root: Path;
    _isDirent: boolean;
    _statsProp: 'dirent' | 'stats';
    _rdOptions: {
        encoding: 'utf8';
        withFileTypes: boolean;
    };
    _fileFilter: Tester;
    _directoryFilter: Tester;
    constructor(options?: Partial<ReaddirpOptions>);
    _read(batch: number): Promise<void>;
    _exploreDir(path: Path, depth: number): Promise<{
        files: string[] | undefined;
        depth: number;
        path: string;
    }>;
    _formatEntry(dirent: PathOrDirent, path: Path): Promise<EntryInfo | undefined>;
    _onError(err: Error): void;
    _getEntryType(entry: EntryInfo): Promise<void | "" | "file" | "directory">;
    _includeAsFile(entry: EntryInfo): boolean | undefined;
}
/**
 * Main function which ends up calling readdirRec and reads all files and directories in given root recursively.
 * @param root Root directory
 * @param options Options to specify root (start directory), filters and recursion depth
 */
export declare const readdirp: (root: Path, options?: Partial<ReaddirpOptions>) => ReaddirpStream;
export declare const readdirpPromise: (root: Path, options?: Partial<ReaddirpOptions>) => Promise<string[]>;
export default readdirp;
