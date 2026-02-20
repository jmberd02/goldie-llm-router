// const express = require('express');
// const cors = require('cors');
// const fetch = require('node-fetch');

// const app = express();
// const PORT = process.env.PORT || 3001;

// // Middleware
// app.use(cors());
// app.use(express.json());

// // Health check endpoint
// app.get('/health', (req, res) => {
//   res.json({ status: 'ok', service: 'copilot-service' });
// });

// // Prompt optimization endpoint
// app.post('/api/optimize-prompt', async (req, res) => {
//   try {
//     const { prompt, context } = req.body;

//     if (!prompt) {
//       return res.status(400).json({ error: 'Prompt is required' });
//     }

//     // Build context-aware system prompt
//     let systemPrompt = `You are an expert Prompt Engineer. Rewrite the user's input to be more detailed, structured, and effective. Improve clarity and add necessary constraints. Return ONLY the improved prompt text without any preamble or explanation.`;

//     // Add context from threshold sliders if provided
//     if (context && context.thresholds) {
//       const thresholdInfo = Object.entries(context.thresholds)
//         .map(([category, value]) => `${category}: ${value}`)
//         .join(', ');
//       systemPrompt += `\n\nConsider these task category thresholds: ${thresholdInfo}`;
//     }

//     // Call Ollama directly using fetch
//     const response = await fetch('http://localhost:11434/api/generate', {
//       method: 'POST',
//       headers: {
//         'Content-Type': 'application/json',
//       },
//       body: JSON.stringify({
//         model: 'qwen2.5:1.5b',
//         prompt: `${systemPrompt}\n\nOriginal prompt: ${prompt}\n\nImproved prompt:`,
//         stream: false,
//         options: {
//           temperature: 0.7,
//           top_p: 0.9,
//         }
//       })
//     });

//     if (!response.ok) {
//       throw new Error(`Ollama API returned ${response.status}`);
//     }

//     const data = await response.json();
//     const optimizedPrompt = data.response.trim();

//     console.log(`✅ Optimized prompt (${prompt.length} → ${optimizedPrompt.length} chars)`);

//     res.json({
//       success: true,
//       original: prompt,
//       optimized: optimizedPrompt,
//       metadata: {
//         model: 'qwen2.5:1.5b',
//         contextUsed: !!context,
//         thresholds: context?.thresholds || null
//       }
//     });

//   } catch (error) {
//     console.error('❌ Optimization error:', error.message);
//     res.status(500).json({
//       success: false,
//       error: error.message || 'Failed to optimize prompt'
//     });
//   }
// });

// // Start server
// app.listen(PORT, () => {
//   console.log(`🚀 CopilotKit service running on http://localhost:${PORT}`);
//   console.log(`📝 Optimize endpoint: http://localhost:${PORT}/api/optimize-prompt`);
//   console.log(`🏥 Health check: http://localhost:${PORT}/health`);
// });
