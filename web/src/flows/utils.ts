export function getQueryVariables(): Record<string, string> {
    const query = window.location.search.substring(1);
    const vars = query.split("&");
    const entries: Record<string, string> = {};
    for (let i = 0; i < vars.length; i++) {
        const pair = vars[i].split("=");
        entries[decodeURIComponent(pair[0])] = decodeURIComponent(pair[1]);
    }
    return entries;
}
