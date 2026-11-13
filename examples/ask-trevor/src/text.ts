// Turning stored text into something safe to hand to a model.
// Guide: guide/03-build.md, "9. Return results as data"; guide/02-design.md, "Results".

// Terminal escape sequences (CSI and OSC), which can hide or rewrite text in a terminal.
const ANSI = /\u001b\[[0-?]*[ -/]*[@-~]|\u001b\][^\u0007\u001b]*(?:\u0007|\u001b\\)/g;
// Control characters other than tab and newline.
const CONTROL = /[\u0000-\u0008\u000b-\u001f\u007f-\u009f]/g;
// Zero-width, bidirectional-control, word-joiner and byte-order-mark characters.
const INVISIBLE = /[­​-‏‪-‮⁠-⁤⁦-⁩﻿]/g;
// Unicode "tag" characters (U+E0000 to U+E007F), used to smuggle invisible text.
const TAGS = /[\u{e0000}-\u{e007f}]/gu;
// HTML comments and tags.
const HTML_COMMENT = /<!--[\s\S]*?-->/g;
const HTML_TAG = /<\/?[a-z][^>]*>/gi;
// Markdown images and links, and bare URLs: a client might load or follow them.
const MD_IMAGE = /!\[([^\]]*)\]\([^)]*\)/g;
const MD_LINK = /\[([^\]]+)\]\([^)]*\)/g;
const URL_LIKE = /\b(?:https?|ftp|file|data|javascript|vbscript):[^\s<>"'\]]+/gi;

/**
 * Plain text for a model to read: no hidden characters, no markup,
 * no links or images that a client could load automatically.
 */
export function plainText(input: string): string {
  return input
    .normalize("NFKC")
    .replace(ANSI, "")
    .replace(HTML_COMMENT, "")
    .replace(HTML_TAG, "")
    .replace(MD_IMAGE, "[image removed]")
    .replace(MD_LINK, "$1")
    .replace(URL_LIKE, "[link removed]")
    .replace(TAGS, "")
    .replace(INVISIBLE, "")
    .replace(CONTROL, "")
    .replace(/[ \t]+/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

/** Shorten text to at most `max` characters, marking the cut. */
export function clip(text: string, max: number): string {
  return text.length <= max ? text : `${text.slice(0, max - 1)}…`;
}
