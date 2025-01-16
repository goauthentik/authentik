/**
 * @typedef {import('type-fest').PackageJson} PackageJson
 */

import fs from 'node:fs'
import path from 'node:path'

/**
 * Get the repository from `package.json`.
 *
 * @param {string} cwd
 *   CWD.
 * @returns {string | undefined}
 *   Repository.
 */
export function getRepoFromPackage(cwd) {
  /** @type {PackageJson | undefined} */
  let pkg

  try {
    pkg = JSON.parse(String(fs.readFileSync(path.join(cwd, 'package.json'))))
  } catch {}

  const repository =
    pkg && pkg.repository
      ? // Object form.
        /* c8 ignore next 2 */
        typeof pkg.repository === 'object'
        ? pkg.repository.url
        : pkg.repository
      : ''

  return repository
}
