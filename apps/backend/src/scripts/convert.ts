#!/usr/bin/env node
import { Command } from 'commander';
import { promises as fs } from 'fs';
import { parse } from 'json2csv';

const program = new Command();
program
  .requiredOption('-i, --input <file>', 'Input JSON file')
  .requiredOption('-o, --output <file>', 'Output CSV file')
  .parse(process.argv);

const opts = program.opts();

async function convert() {
  const data = JSON.parse(await fs.readFile(opts.input, 'utf8'));
  const csv = parse(data);
  await fs.writeFile(opts.output, csv);
}

convert().catch(err => {
  console.error(err);
  process.exit(1);
});
