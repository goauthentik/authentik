import process from 'node:process';

const packageJson = process.env.npm_package_json;
const userAgent = process.env.npm_config_user_agent;
const isNpm6 = Boolean(userAgent && userAgent.startsWith('npm'));
const isNpm7 = Boolean(packageJson && packageJson.endsWith('package.json'));

export const isNpm = isNpm6 || isNpm7;
export const isYarn = Boolean(userAgent && userAgent.startsWith('yarn'));
export const isNpmOrYarn = isNpm || isYarn;
