declare namespace isAsyncFunction {
    type AsyncFunction = (...args: any[]) => Promise<any>
}

declare function isAsyncFunction(fn: unknown): fn is isAsyncFunction.AsyncFunction;

export = isAsyncFunction;