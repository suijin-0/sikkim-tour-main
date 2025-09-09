// server.js
const express = require("express");
const cors = require("cors");

const app = express();
app.use(cors());
app.use(express.json());

app.post("/chat", async (req, res) => {
  try {
    const { message } = req.body;

    const response = await fetch("http://localhost:11434/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: "mistral",   // or mistral, llama2
        prompt: message,
        stream: true    // streaming enabled
      })
    });

    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split("\n").filter(line => line.trim() !== "");
      for (const line of lines) {
        try {
          const json = JSON.parse(line);
          if (json.response) {
            res.write(`data: ${json.response}\n\n`);
          }
          if (json.done) {
            res.write("data: [DONE]\n\n");
            res.end();
            return;
          }
        } catch (e) {
          console.error("Parse error:", e);
        }
      }
    }
  } catch (err) {
    console.error("Error:", err);
    res.status(500).json({ error: "Failed to connect to Ollama" });
  }
});

app.listen(3000, () => {
  console.log("✅ Streaming server running at http://localhost:3000");
});
