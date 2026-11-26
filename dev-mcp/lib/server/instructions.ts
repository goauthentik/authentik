/**
 * @file The server instructions clients put in front of the model.
 *   The first 512 characters carry the rules: Codex only guarantees that much.
 */

export const INSTRUCTIONS = `\
Use these tools to check authentik changes before you report them done. Call akdev_generated \
after changing models, serializers or API views. Call akdev_lint with no paths to lint the whole \
change. Use akdev_skill to read a repo skill before answering how-to questions. Results list what \
they skipped and couldn't tell; repeat that when you summarize. Nothing here applies changes or \
contacts GitHub.

Tool guide:
- akdev_status first: it shows how this machine runs Postgres and containers, and whether the \
database guard allowed the database tools. If a tool is missing, the guard said why.
- If the guard says Postgres isn't running and akdev_services is listed, ask the person, then \
call it with action 'up' to start the dev containers from scripts/compose.yml.
- akdev_generated and akdev_lint can take minutes. They return a jobId; poll akdev_job.
- Commands in results are written for this machine's setup. Show them to the person rather than \
running ones that change the database.
- A result's \`unknown\` list means the tool couldn't tell. Don't report those items as passing.
`;
