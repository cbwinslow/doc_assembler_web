import { Router } from 'express';
import { vectorService } from '@/services/vectorService.js';
import { aiConfig } from '@/config/config.js';
import { logger } from '@/utils/logger.js';

const router = Router();

router.post('/query', async (req, res) => {
  const { query } = req.body as { query?: string };
  if (!query) {
    return res.status(400).json({ error: 'Query is required' });
  }

  try {
    const results = await vectorService.searchSimilarDocuments(query, { limit: 5 });
    const context = results.map(r => r.metadata.text).join('\n');

    let answer = 'No language model configured';
    if (aiConfig.openai.apiKey) {
      const { OpenAI } = await import('openai');
      const openai = new OpenAI({ apiKey: aiConfig.openai.apiKey });
      const completion = await openai.chat.completions.create({
        model: aiConfig.openai.model,
        messages: [
          { role: 'system', content: 'Answer the question using the provided context.' },
          { role: 'user', content: `Context:\n${context}\n\nQuestion: ${query}` }
        ]
      });
      answer = completion.choices[0]?.message?.content || '';
    }

    res.json({ answer, sources: results });
  } catch (error) {
    logger.error('RAG query failed:', error);
    res.status(500).json({ error: 'RAG query failed' });
  }
});

export default router;
