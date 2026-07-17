"use strict";

const { fnv64 } = require("@s4tk/hashing");

/** Group used for every resource this tool generates. Kept at 0 (no group
 * override) since the synthetic/real CASP template already scopes its own
 * resources; we only need unique instances. */
const DEFAULT_GROUP = 0;

/**
 * Derives a deterministic 64-bit resource instance ID from a Sim name and a
 * purpose-specific salt (e.g. "texture" or "casp"), so re-running the CLI for
 * the same Sim reproducibly targets the same resource instance.
 *
 * @param {string} simName
 * @param {string} salt
 * @returns {bigint}
 */
function deriveInstanceId(simName, salt) {
  return fnv64(`photoface:${salt}:${simName}`, true);
}

module.exports = { DEFAULT_GROUP, deriveInstanceId };
