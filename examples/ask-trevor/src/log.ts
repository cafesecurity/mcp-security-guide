// Structured tool-call logs: who did what, not what they saw.
// Guide: guide/06-deploy-operate.md, "Logs".

export interface ToolCallEvent {
  time: string;
  event: "tool_call";
  user: string;
  tenant: string;
  client: string;
  tool: string;
  arguments: Record<string, unknown>;
  resultCount: number;
  resultBytes: number;
  outcome: "ok" | "not_found" | "denied" | "error";
  tokenId?: string;
}

export type LogSink = (event: ToolCallEvent) => void;

/** Default sink: one JSON line per event on stderr (stdout may be an MCP transport). */
export const stderrSink: LogSink = (event) => {
  process.stderr.write(`${JSON.stringify(event)}\n`);
};

const SENSITIVE_KEY = /token|secret|password|authorization|cookie|key/i;
const MAX_VALUE = 200;

/** Mask sensitive-looking keys and shorten long values before logging. */
export function maskArguments(args: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(args)) {
    if (SENSITIVE_KEY.test(k)) out[k] = "[masked]";
    else if (typeof v === "string" && v.length > MAX_VALUE) out[k] = `${v.slice(0, MAX_VALUE)}…`;
    else out[k] = v;
  }
  return out;
}
