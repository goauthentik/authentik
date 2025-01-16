import {createAutomaticRuntime} from './create-automatic-runtime.js'
import {h} from './index.js'

// Export `JSX` as a global for TypeScript.
export * from './jsx-automatic.js'

export const {Fragment, jsx, jsxDEV, jsxs} = createAutomaticRuntime(h)
