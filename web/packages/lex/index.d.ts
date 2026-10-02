export type Token = unknown;

export type LexerAction = (
    this: Lexer,
    match: string,
    ...captures: string[]
) => Token | Token[] | null | void;

export type DefunctHandler = (this: Lexer, chr: string) => Token | Token[] | null | void;

export class Lexer {
    state: number;
    index: number;
    input: string;
    reject: boolean;

    constructor(defunct?: DefunctHandler);
    addRule(pattern: RegExp, action: LexerAction, start?: number[]): this;
    setInput(input: string): this;
    lex(): Token | null;
}

export default Lexer;
