import type {Program} from 'estree'

export {mdxExpression, type Options} from './lib/syntax.js'

declare module 'micromark-util-types' {
  // eslint-disable-next-line @typescript-eslint/consistent-type-definitions
  interface Token {
    estree?: Program
  }

  // eslint-disable-next-line @typescript-eslint/consistent-type-definitions
  interface TokenTypeMap {
    mdxFlowExpression: 'mdxFlowExpression'
    mdxFlowExpressionMarker: 'mdxFlowExpressionMarker'
    mdxFlowExpressionChunk: 'mdxFlowExpressionChunk'

    mdxTextExpression: 'mdxTextExpression'
    mdxTextExpressionMarker: 'mdxTextExpressionMarker'
    mdxTextExpressionChunk: 'mdxTextExpressionChunk'
  }
}
