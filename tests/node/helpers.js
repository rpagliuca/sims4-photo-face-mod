"use strict";

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const TEMPLATE_PATH = path.join(__dirname, "..", "..", "packages", "casp_template", "base.package");

function makeTmpDir(t) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "photoface-test-"));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  return dir;
}

module.exports = { TEMPLATE_PATH, makeTmpDir };
