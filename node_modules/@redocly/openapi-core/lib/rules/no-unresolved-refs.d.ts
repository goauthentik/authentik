import { Oas3Rule } from '../visitors';
import { ResolveResult, Problem } from '../walk';
import { Location } from '../ref-utils';
export declare const NoUnresolvedRefs: Oas3Rule;
export declare function reportUnresolvedRef(resolved: ResolveResult<any>, report: (m: Problem) => void, location: Location): void;
