export const isSafari = () =>
    navigator.userAgent.includes("Safari") && !navigator.userAgent.includes("Chrome");

export default isSafari;
