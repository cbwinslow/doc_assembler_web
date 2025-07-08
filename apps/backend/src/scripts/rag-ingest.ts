#!/usr/bin/env node
import { Command } from 'commander';
import { promises as fs } from 'fs';
import { join, extname } from 'path';
import { RecursiveCharacterTextSplitter } from '@langchain/textsplitters';
import { vectorService } from '@/services/vectorService.js';
import { logger } from '@/utils/logger.js';

const program = new Command();
program.argument('<dir>', 'Directory to ingest').parse(process.argv);
const [dir] = program.args;

/**
 * Processes all `.txt` and `.md` files in the specified directory, splits their content into overlapping text chunks, generates embeddings for each chunk, and stores the embeddings with associated metadata.
 *
 * Logs progress after each file is ingested. Exits the process with a failure code if an error occurs.
 */
async function ingest() {
  const files = await fs.readdir(dir);
  for (const file of files) {
    const path = join(dir, file);
    const ext = extname(file).toLowerCase();
    if (!['.txt', '.md'].includes(ext)) continue;
    const text = await fs.readFile(path, 'utf8');
    const splitter = new RecursiveCharacterTextSplitter({ chunkSize: 1000, chunkOverlap: 200 });
    const docs = await splitter.createDocuments([text]);
    for (const d of docs) {
      const embeddings = await vectorService.generateEmbeddings(d.pageContent);
      await vectorService.storeDocumentEmbeddings(
        `${file}-${Math.random().toString(36).slice(2,8)}`,
        embeddings,
        { text: d.pageContent, title: file, type: ext.substring(1), userId: 'system' }
      );
    }
    logger.info(`Ingested ${file}`);
  }
}

ingest().catch(err => {
  logger.error('Ingest failed', err);
  process.exit(1);
});
