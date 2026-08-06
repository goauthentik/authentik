/* eslint-disable func-names */
import { Lexer } from "lex";
import { describe, expect, it, vi } from "vitest";

const drain = (lexer: Lexer): unknown[] => {
    const out: unknown[] = [];
    let token: unknown;

    while ((token = lexer.lex()) !== null) {
        out.push(token);
    }
    return out;
};

describe("Lexer", () => {
    describe("addRule", () => {
        it("returns the lexer for chaining", () => {
            const lexer = new Lexer();
            expect(lexer.addRule(/a/, () => "a")).toBe(lexer);
        });

        it("preserves multiline, ignoreCase, and unicode flags when re-compiling", () => {
            const lexer = new Lexer(() => null);
            const seen: string[] = [];

            lexer.addRule(/^a/im, (m) => {
                seen.push(m);
            });
            lexer.setInput("A\nA");

            drain(lexer);
            expect(seen).toEqual(["A", "A"]);
        });

        it("matches unicode patterns", () => {
            const lexer = new Lexer();
            lexer.addRule(/\p{Letter}+/u, (m) => m);
            lexer.setInput("café");

            expect(lexer.lex()).toBe("café");
        });
    });

    describe("setInput", () => {
        it("resets state, index, and pending tokens", () => {
            const lexer = new Lexer();
            lexer.addRule(/./, (c) => c);

            lexer.setInput("ab");
            expect(lexer.lex()).toBe("a");
            lexer.state = 7;

            lexer.setInput("xy");
            expect(lexer.state).toBe(0);
            expect(lexer.index).toBe(0);
            expect(lexer.lex()).toBe("x");
            expect(lexer.lex()).toBe("y");
        });

        it("returns the lexer for chaining", () => {
            const lexer = new Lexer();
            expect(lexer.setInput("")).toBe(lexer);
        });
    });

    describe("tokenization", () => {
        it("tokenizes a simple expression", () => {
            const lexer = new Lexer();
            lexer
                .addRule(/\s+/, () => null)
                .addRule(/[a-zA-Z]+/, (m) => ({ type: "ident", value: m }))
                .addRule(/\d+/, (m) => ({ type: "num", value: Number(m) }))
                .addRule(/[+\-*/]/, (m) => ({ type: "op", value: m }));

            lexer.setInput("foo + 12 * bar");
            expect(drain(lexer)).toEqual([
                { type: "ident", value: "foo" },
                { type: "op", value: "+" },
                { type: "num", value: 12 },
                { type: "op", value: "*" },
                { type: "ident", value: "bar" },
            ]);
        });

        it("skips matches whose action returns null", () => {
            const lexer = new Lexer();
            lexer.addRule(/\s+/, () => null).addRule(/\S+/, (m) => m);

            lexer.setInput("   foo   bar   ");
            expect(drain(lexer)).toEqual(["foo", "bar"]);
        });

        it("returns null once the input is exhausted", () => {
            const lexer = new Lexer();
            lexer.addRule(/./, (c) => c);
            lexer.setInput("a");

            expect(lexer.lex()).toBe("a");
            expect(lexer.lex()).toBeNull();
            expect(lexer.lex()).toBeNull();
        });

        it("passes capture groups to the action", () => {
            const lexer = new Lexer();
            const calls: string[][] = [];

            lexer.addRule(/(\w+)=(\w+)/, (...args) => {
                calls.push(args);
                return args[0];
            });

            lexer.setInput("foo=bar");
            lexer.lex();
            expect(calls).toEqual([["foo=bar", "foo", "bar"]]);
        });

        it("binds `this` to the lexer inside the action", () => {
            const lexer = new Lexer();
            let captured: Lexer | undefined;

            lexer.addRule(/a/, function () {
                // eslint-disable-next-line consistent-this, @typescript-eslint/no-this-alias
                captured = this;
                return "a";
            });

            lexer.setInput("a");
            lexer.lex();
            expect(captured).toBe(lexer);
        });
    });

    describe("longest-match tie-breaking", () => {
        it("prefers the longer non-global match", () => {
            const lexer = new Lexer();
            lexer.addRule(/if/, () => "KW_IF").addRule(/iffy/, () => "IDENT_IFFY");

            lexer.setInput("iffy");
            expect(lexer.lex()).toBe("IDENT_IFFY");
        });

        it("treats global rules as fallbacks behind non-global rules of the same length", () => {
            const lexer = new Lexer();
            lexer.addRule(/[a-z]+/g, (m) => `g:${m}`).addRule(/foo/, (m) => `s:${m}`);

            lexer.setInput("foo");
            expect(lexer.lex()).toBe("s:foo");
        });
    });

    describe("multi-token return", () => {
        it("yields the first token immediately and queues the rest", () => {
            const lexer = new Lexer();
            lexer.addRule(/a/, () => ["A1", "A2", "A3"]);

            lexer.setInput("a");
            expect(lexer.lex()).toBe("A1");
            expect(lexer.lex()).toBe("A2");
            expect(lexer.lex()).toBe("A3");
            expect(lexer.lex()).toBeNull();
        });

        it("drains the queue before scanning further input", () => {
            const lexer = new Lexer();
            lexer.addRule(/a/, () => ["A1", "A2"]).addRule(/b/, () => "B");

            lexer.setInput("ab");
            expect(drain(lexer)).toEqual(["A1", "A2", "B"]);
        });
    });

    describe("reject", () => {
        it("falls through to the next-best match when an action sets reject", () => {
            const lexer = new Lexer();
            const order: string[] = [];

            lexer
                .addRule(/foo/, function () {
                    order.push("first");
                    this.reject = true;
                })
                .addRule(/foo/, () => {
                    order.push("second");
                    return "FOO";
                });

            lexer.setInput("foo");
            expect(lexer.lex()).toBe("FOO");
            expect(order).toEqual(["first", "second"]);
        });

        it("rolls back the lexer index when an action rejects", () => {
            const lexer = new Lexer();

            lexer
                .addRule(/abc/, function () {
                    this.reject = true;
                })
                .addRule(/a/, (m) => m);

            lexer.setInput("abc");
            expect(lexer.lex()).toBe("a");
            expect(lexer.index).toBe(1);
        });
    });

    describe("defunct handling", () => {
        it("throws by default on unexpected characters", () => {
            const lexer = new Lexer();
            lexer.addRule(/a/, (m) => m);

            lexer.setInput("a@");
            expect(lexer.lex()).toBe("a");
            expect(() => lexer.lex()).toThrow(/Unexpected character at index 1: @/);
        });

        it("invokes a custom defunct handler with the offending character", () => {
            const defunct = vi.fn((chr: string) => `?${chr}`);
            const lexer = new Lexer(defunct);
            lexer.addRule(/a/, (m) => m);

            lexer.setInput("a@b");
            expect(drain(lexer)).toEqual(["a", "?@", "?b"]);
            expect(defunct).toHaveBeenCalledTimes(2);
            expect(defunct.mock.calls[0]?.[0]).toBe("@");
        });

        it("ignores defunct return values that are null", () => {
            const lexer = new Lexer((_chr) => null);
            lexer.addRule(/a/, (m) => m);

            lexer.setInput("@@a");
            expect(lexer.lex()).toBe("a");
            expect(lexer.lex()).toBeNull();
        });

        it("supports array returns from the defunct handler", () => {
            const lexer = new Lexer((chr) => [`bad:${chr}`, "extra"]);
            lexer.addRule(/a/, (m) => m);

            lexer.setInput("@");
            expect(lexer.lex()).toBe("bad:@");
            expect(lexer.lex()).toBe("extra");
        });

        it("falls back to the default handler when given a non-function", () => {
            // @ts-expect-error — exercising the runtime guard
            const lexer = new Lexer("not a function");
            lexer.setInput("@");
            expect(() => lexer.lex()).toThrow(/Unexpected character/);
        });
    });

    describe("states", () => {
        it("only fires rules whose start array includes the current state", () => {
            const lexer = new Lexer();

            lexer
                .addRule(/"/, function () {
                    this.state = 2;
                })
                .addRule(
                    /"/,
                    function () {
                        this.state = 0;
                    },
                    [2],
                )
                .addRule(/[^"]+/, (m) => `STR:${m}`, [2])
                .addRule(/[a-z]+/, (m) => `ID:${m}`);

            lexer.setInput('foo"hello"bar');
            expect(drain(lexer)).toEqual(["ID:foo", "STR:hello", "ID:bar"]);
        });

        it("treats an empty start array as 'active in any state'", () => {
            const lexer = new Lexer();

            lexer
                .addRule(/!/, function () {
                    this.state = 5;
                    return "BANG";
                })
                .addRule(/./, (m) => m, []);

            lexer.setInput("a!b");
            expect(drain(lexer)).toEqual(["a", "BANG", "b"]);
        });

        it("matches inclusive `[0]` rules from odd-numbered states", () => {
            const lexer = new Lexer();

            lexer
                .addRule(/#/, function () {
                    this.state = 1;
                })
                .addRule(/[a-z]+/, (m) => m);

            lexer.setInput("ab#cd");
            expect(drain(lexer)).toEqual(["ab", "cd"]);
        });

        it("does not match `[0]` rules from even non-zero states", () => {
            const lexer = new Lexer();

            lexer
                .addRule(/#/, function () {
                    this.state = 2;
                })
                .addRule(/[a-z]+/, (m) => m);

            lexer.setInput("ab#cd");
            expect(lexer.lex()).toBe("ab");
            expect(() => lexer.lex()).toThrow(/Unexpected character/);
        });
    });
});
