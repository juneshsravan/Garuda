/**
 * dev-tools.ts
 *
 * Controls whether the in-page state-switcher (Normal / Loading / Empty / Error)
 * is rendered. Set NEXT_PUBLIC_SHOW_DEV_TOOLS=true in your local .env.local to
 * enable it. The variable must NOT be set in production or in frontend/.env.local
 * as checked into version control.
 */
export const showDevTools =
  process.env.NEXT_PUBLIC_SHOW_DEV_TOOLS === "true";
