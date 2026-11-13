// A per-user rate limit. In production, enforce this at the gateway as well,
// with a store shared across instances.
// Guide: guide/06-deploy-operate.md, "Rate limits and caps".

import type { RequestHandler } from "express";

export interface RateLimitOptions {
  /** Requests allowed per window, per user. */
  limit: number;
  /** Window length in milliseconds. */
  windowMs: number;
  now?: () => number;
}

export function perUserRateLimit(opts: RateLimitOptions): RequestHandler {
  const now = opts.now ?? Date.now;
  const windows = new Map<string, { start: number; count: number }>();

  return (req, res, next) => {
    const sub = req.auth?.extra?.sub;
    // Runs after authentication; an unauthenticated request never gets here.
    const key = typeof sub === "string" ? sub : "anonymous";
    const t = now();
    const w = windows.get(key);
    if (!w || t - w.start >= opts.windowMs) {
      windows.set(key, { start: t, count: 1 });
      return next();
    }
    if (w.count >= opts.limit) {
      res.setHeader("Retry-After", Math.ceil((w.start + opts.windowMs - t) / 1000).toString());
      res.status(429).json({ error: "rate_limited" });
      return;
    }
    w.count += 1;
    next();
  };
}
