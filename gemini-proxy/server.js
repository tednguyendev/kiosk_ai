const express = require('express');
const { GoogleGenerativeAI } = require('@google/generative-ai');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3100;
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET || 'kiosk-ai-secret';

if (!GEMINI_API_KEY) {
  console.error('GEMINI_API_KEY env var is required');
  process.exit(1);
}

const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);

// Auth middleware — accepts x-api-key header OR Bearer token (OpenAI-compatible)
function authorize(req, res, next) {
  const xApiKey = req.headers['x-api-key'];
  const authHeader = req.headers['authorization'] || '';
  const bearerToken = authHeader.startsWith('Bearer ') ? authHeader.slice(7) : null;
  if (xApiKey !== WEBHOOK_SECRET && bearerToken !== WEBHOOK_SECRET) {
    return res.status(401).json({ error: { message: 'Unauthorized', code: '401', type: 'Unauthorized', status: 401 } });
  }
  next();
}

// Convert OpenAI-style messages to Gemini format
function toGeminiContents(messages) {
  const systemParts = [];
  const contents = [];

  for (const msg of messages) {
    if (msg.role === 'system') {
      systemParts.push(msg.content);
    } else {
      contents.push({
        role: msg.role === 'assistant' ? 'model' : 'user',
        parts: [{ text: msg.content }]
      });
    }
  }

  // Gemini requires conversation to start with a user message
  // If first non-system message is from model, prepend a dummy user turn
  if (contents.length > 0 && contents[0].role === 'model') {
    contents.unshift({ role: 'user', parts: [{ text: '.' }] });
  }

  return { systemInstruction: systemParts.join('\n\n') || undefined, contents };
}

// OpenAI-compatible endpoint (D-ID Custom LLM hits this)
app.post('/v1/chat/completions', authorize, handleChat);
app.post('/llm', authorize, handleChat);

async function handleChat(req, res) {
  const { messages, stream } = req.body;

  if (!messages || !messages.length) {
    return res.status(400).json({ error: { message: 'No messages provided', status: 400 } });
  }

  const { systemInstruction, contents } = toGeminiContents(messages);

  const model = genAI.getGenerativeModel({
    model: 'gemini-2.0-flash',
    ...(systemInstruction && { systemInstruction })
  });

  try {
    if (stream) {
      // Streaming SSE response
      res.setHeader('Content-Type', 'text/event-stream');
      res.setHeader('Cache-Control', 'no-cache');
      res.setHeader('Connection', 'keep-alive');

      const result = await model.generateContentStream({ contents });
      let id = 0;

      for await (const chunk of result.stream) {
        const text = chunk.text();
        if (text) {
          id++;
          const data = JSON.stringify({
            id: String(id),
            created: Math.floor(Date.now() / 1000),
            choices: [{ delta: { content: text } }]
          });
          res.write(`data: ${data}\n\n`);
        }
      }

      res.write('data: [DONE]\n\n');
      res.end();
    } else {
      // Non-streaming response
      const result = await model.generateContent({ contents });
      const text = result.response.text();
      res.json({ content: text });
    }
  } catch (err) {
    console.error('Gemini error:', err);
    if (!res.headersSent) {
      res.status(500).json({ error: { message: err.message, status: 500 } });
    } else {
      res.end();
    }
  }
}

// Health check
app.get('/health', (req, res) => res.json({ status: 'ok' }));

app.listen(PORT, () => {
  console.log(`Gemini proxy running on port ${PORT}`);
});
