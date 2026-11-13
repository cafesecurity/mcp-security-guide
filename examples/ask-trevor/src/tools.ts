// The two read-only tools. One McpServer is built per request, for one verified caller.
// Guide: guide/02-design.md ("Tool descriptions", "Results", "Reads and writes");
//        guide/03-build.md ("5. Strict input schemas", "9. Return results as data").

import { McpServer, type AuthInfo } from "@modelcontextprotocol/server";
import * as z from "zod";
import { callerFrom } from "./auth.js";
import type { Doc, DocStore } from "./corpus.js";
import { maskArguments, type LogSink, type ToolCallEvent } from "./log.js";
import { clip, plainText } from "./text.js";

export const SERVER_NAME = "ask-trevor-example";
export const SERVER_VERSION = "0.1.0";

const MAX_RESULTS = 25;
const EXCERPT_CHARS = 400;
const BODY_CHARS = 4000;

// Strict schemas: bounded strings, integer ranges, no unknown properties.
const SearchDocsInput = z
  .object({
    query: z.string().min(1).max(200).describe("Words to look for in document titles and text."),
    limit: z.number().int().min(1).max(MAX_RESULTS).default(10).describe("Maximum number of results, 1 to 25."),
  })
  .strict();

const GetDocInput = z
  .object({
    id: z
      .string()
      .regex(/^doc-[a-z0-9-]{1,60}$/)
      .describe("A document ID returned by search_docs, such as doc-holiday-policy."),
  })
  .strict();

/** Every result says where its text came from, so clients and models can treat outsiders' text as data. */
function source(doc: Doc): "internal" | "external" {
  return doc.external ? "external" : "internal";
}

function textResult(value: unknown) {
  const text = JSON.stringify(value);
  return { text, result: { content: [{ type: "text" as const, text }] } };
}

export interface ToolDeps {
  store: DocStore;
  log: LogSink;
}

export function buildServer(auth: AuthInfo | undefined, deps: ToolDeps): McpServer {
  const caller = callerFrom(auth); // user, tenant and groups from the verified token only
  const server = new McpServer({ name: SERVER_NAME, version: SERVER_VERSION });

  const record = (tool: string, args: Record<string, unknown>, outcome: ToolCallEvent["outcome"], count: number, bytes: number) =>
    deps.log({
      time: new Date().toISOString(),
      event: "tool_call",
      user: caller.sub,
      tenant: caller.tenant,
      client: auth?.clientId ?? "unknown",
      tool,
      arguments: maskArguments(args),
      resultCount: count,
      resultBytes: bytes,
      outcome,
      tokenId: typeof auth?.extra?.jti === "string" ? auth.extra.jti : undefined,
    });

  // Descriptions are plain documentation: what it does, its parameters, what it returns.
  // They never address the model and never mention other servers or tools.
  server.registerTool(
    "search_docs",
    {
      title: "Search documents",
      description:
        "Searches the documents the signed-in user is allowed to read. Returns up to 25 matches, " +
        "each with its ID, title, a short plain-text excerpt and its source: internal, or external " +
        "when the author is outside the organisation.",
      inputSchema: SearchDocsInput,
      annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false },
    },
    async ({ query, limit }) => {
      const docs = deps.store.search(caller, query, Math.min(limit, MAX_RESULTS));
      const { text, result } = textResult({
        results: docs.map((d) => ({
          id: d.id,
          title: plainText(d.title),
          source: source(d),
          updated: d.updated,
          excerpt: clip(plainText(d.body), EXCERPT_CHARS),
        })),
      });
      record("search_docs", { query, limit }, "ok", docs.length, text.length);
      return result;
    },
  );

  server.registerTool(
    "get_doc",
    {
      title: "Get a document",
      description:
        "Returns one document the signed-in user is allowed to read, by ID: its title, author, " +
        "source (internal or external), last update date and plain-text body. Returns not_found " +
        "if the document does not exist or the user may not read it.",
      inputSchema: GetDocInput,
      annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false },
    },
    async ({ id }) => {
      const doc = deps.store.get(caller, id);
      if (!doc) {
        const { text, result } = textResult({ error: "not_found" });
        record("get_doc", { id }, "not_found", 0, text.length);
        return result;
      }
      const { text, result } = textResult({
        id: doc.id,
        title: plainText(doc.title),
        author: doc.author,
        source: source(doc),
        updated: doc.updated,
        body: clip(plainText(doc.body), BODY_CHARS),
      });
      record("get_doc", { id }, "ok", 1, text.length);
      return result;
    },
  );

  return server;
}
