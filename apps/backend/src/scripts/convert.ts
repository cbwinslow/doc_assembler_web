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

/**
 * Converts a JSON file specified by the input option to a CSV file at the output path.
 *
 * Reads the input JSON file, parses its contents, converts the data to CSV format, and writes the result to the output file.
 */
async function convert() {
  const data = JSON.parse(await fs.readFile(opts.input, 'utf8'));
  const csv = parse(data);
  await fs.writeFile(opts.output, csv);
}

convert().catch(err => {
  console.error(err);
  process.exit(1);
});
