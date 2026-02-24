/**
 * Platform detection utilities
 */

// Simple platform detection - detects macOS based on userAgent and navigator.platform
export const isMac = (): boolean => {
  if (typeof window === 'undefined') return false;

  const platform = window.navigator.platform;
  const userAgent = window.navigator.userAgent;

  // Check for macOS platforms and user agent indicators
  const isMacPlatform = /Mac|Macintosh|MacIntel|MacPPC|Mac68K/i.test(platform);
  const isMacUserAgent = /Mac OS X|macOS/i.test(userAgent);

  return isMacPlatform || isMacUserAgent;
};