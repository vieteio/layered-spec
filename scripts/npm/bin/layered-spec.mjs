#!/usr/bin/env node

import { main } from "../src/cli.mjs";

main(process.argv.slice(2)).catch((error) => {
  process.stderr.write(`layered-spec: ${error.message}\n`);
  process.exitCode = 1;
});
