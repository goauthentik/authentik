# 01 Foundations: Code Quality

Date: 2026-05-02 (May 2st, 2026)

## Code Linting

We _like_ our guardrails. We use ESLint with as many plug-ins as we can reasonably stuff into it for
our checks, such as `eslint-plugin-lit` and `eslint-plugin-wc`, plus `lit-analyzer`.

## Code Formatting

We use `prettier` to enforce a coding style and to catch some fundamental syntax errors. The current
`prettier` configuration correctly formats Lit's HTML-in-JS and CSS-it-JS use cases, as well as all
the Typescript we can throw at it.

## Lockfile

We have a custom script in `./scripts/lint-lockfile.sh` that checks to ensure that every packages as
a resolved hash.

## Type Checking

Although we use ESBuild to convert and bundle our Typescript into JavaScript, we use the stock
Typescript compiler, `tsc`, to check our types. We maintain a default configuration with `use
strict`.

## Testing

We do have tests, but they are primitive. We are very much in a move-fast and try hard not to break
things. We strongly recommend that every PR include a description of how a peer would test the
product manually to validate that it does what the PR claims it does.

Adding to the library of end-to-end tests is a critical mission.

## Your eyes, and the eyes of your peers

For all that we do like our guardrails, nothing surpasses peer review.

## AI Review

We have had mixed results using AI tools such as Claude and Copilot to vet our code. Claude,
especially, can be very good at pointing out shortcomings and missed opportunities in a pull
request, but it can also generate a lot of false positives or trivial issues. We recommend reading
AI reviews with caution.

## AI Review Strategy

That said, this is the current template for a code review prompt. Start with the _target_ branch,
then download the patch file into the project root. You can easily download the patch file by
navigating to the Github PR and appending `.patch` to it, for example:
`https://github.com/goauthentik/authentik/pull/21868.patch`

We use this template:

> Keep the tone neutral-professional-skeptical, the voice of an expert. Avoid excessive enthusiasm.
> This is the root folder for the authentik single sign-on server.
>
> Read the patch file `./21867.patch`. This [community-provided] patch [describe the patch here in
> > your own words, using only one or two sentences].
>
> Task 1: Provide a high-level summary of the effect of applying `./21868.patch` Point out any
> shortcomings or security considerations.
>
> Task2: If no tests are provided in the patch, describe how these changes could be tested.

Edit the patch number, add or remove "community-provided" as needed, and include your best
understanding of what the patch claims to do in the second paragraph. Having a strong template that
you hand-edit before running seems to work much better than using a generic template in a Claude
skill.
