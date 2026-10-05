import path from 'node:path';

function normalizedWindowsPath(value) {
  const text = String(value || '').trim().replace(/^"|"$/g, '');
  if (!text) return '';
  const normalized = path.win32.normalize(text);
  const withoutTrailingSeparator = normalized.length > 3
    ? normalized.replace(/[\\/]+$/, '')
    : normalized;
  return withoutTrailingSeparator.toLocaleLowerCase('en-US');
}

export function sameTdxRoot(left, right) {
  const normalizedLeft = normalizedWindowsPath(left);
  return Boolean(normalizedLeft) && normalizedLeft === normalizedWindowsPath(right);
}

/**
 * Select the TDX installation that is actually running when it can be
 * identified. A still-existing saved path must not shadow a TDX process on a
 * different drive. Saved paths remain the fallback when no client is running.
 */
export function selectTdxRoot({ configuredRoots = [], runningRoots = [], isValidRoot = () => true } = {}) {
  const uniqueValid = (roots) => {
    const seen = new Set();
    return roots.filter((value) => {
      const root = String(value || '').trim();
      const normalized = normalizedWindowsPath(root);
      if (!normalized || seen.has(normalized) || !isValidRoot(root)) return false;
      seen.add(normalized);
      return true;
    });
  };

  const configured = uniqueValid(configuredRoots);
  const running = uniqueValid(runningRoots);
  if (running.length === 1) return running[0];
  if (running.length > 1) {
    return configured.find((root) => running.some((activeRoot) => sameTdxRoot(root, activeRoot)))
      || running[0];
  }
  return configured[0] || '';
}
