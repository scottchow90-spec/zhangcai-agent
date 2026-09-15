#!/usr/bin/env node

/**
 * Verify that the production HTML can actually hydrate.
 *
 * A Vinext/React page can return HTTP 200 while still being unusable when
 * stale SSR HTML points at chunks from an older build. In that state the
 * browser shows the server-rendered page, but no client event handlers are
 * installed, so every button appears dead. This probe deliberately fetches
 * the HTML and every local _next/static asset it references.
 */

const baseUrl = process.argv[2] ?? "http://127.0.0.1:3003/";

function fail(message) {
  console.error(`[verify-served-assets] ${message}`);
  process.exitCode = 1;
}

try {
  const pageUrl = new URL(baseUrl);
  pageUrl.searchParams.set("_asset_probe", Date.now().toString(36));
  const response = await fetch(pageUrl, {
    headers: {
      "cache-control": "no-cache",
      pragma: "no-cache",
    },
  });

  if (!response.ok) {
    fail(`page returned HTTP ${response.status}`);
  } else {
    const html = await response.text();
    const assetUrls = new Set();
    const assetPattern = /(?:src|href)=["']([^"']+_next\/static\/[^"']+)["']/g;

    for (const match of html.matchAll(assetPattern)) {
      const assetUrl = new URL(match[1], pageUrl);
      if (assetUrl.origin === pageUrl.origin) {
        assetUrls.add(assetUrl);
      }
    }

    if (assetUrls.size === 0) {
      fail("page contains no local _next/static assets; hydration cannot be verified");
    } else {
      const missing = [];
      for (const assetUrl of assetUrls) {
        const assetResponse = await fetch(assetUrl, {
          headers: {
            "cache-control": "no-cache",
            pragma: "no-cache",
          },
        });
        if (!assetResponse.ok) {
          missing.push(`${assetResponse.status} ${assetUrl.pathname}`);
        }
      }

      if (missing.length > 0) {
        fail(`missing or unavailable client assets:\n${missing.join("\n")}`);
      } else {
        console.log(`[verify-served-assets] OK: ${assetUrls.size} client assets are reachable`);
      }
    }
  }
} catch (error) {
  fail(error instanceof Error ? error.message : String(error));
}
