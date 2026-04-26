CCDD #16. Slug: cc-deep-dive-16-the-local-showdown.

Title: Claude Code Deep Dive - The Local Showdown

Bottom line: Even the latest open MoE models (Qwen 3.6 35B-A3B and Gemma 4 26B) running locally on my 36 GB M4 Max were not great with one simple task compared to Claude Code with Opus 4.7 or OpenAI Codex on the same trivial prompt. Cloud frontier models answered in 2-3 seconds. The local MoE models took over a minute, and Gemma 4 ignored the explicit 100-word constraint in this run.

This is a deliberately simple, short article. No deep benchmarking. One trivial prompt, four contestants, four timings, one workflow-level impression.

Series index: Single link to the Medium CCDD series list (https://medium.com/@the.gigi/list/claude-code-deep-dive-5f842373dcaa).

Date: 2026-04-25

Categories: Claude, ClaudeCode, AICoding, AIAgent, LocalModels, Ollama, Qwen, Gemma

Closing greeting: Greek. Flag emoji 🇬🇷. "Αντίο, φίλοι!" (Antío, fíloi!).

Key content points:

1. The Promise. Local models are pitched on three things: privacy (your code stays on your machine), cost (no API bill), and offline availability. With Ollama v0.14.0+ now exposing an Anthropic-compatible Messages API on localhost:11434, Claude Code itself can drive a local model with no proxy. Two new MoE releases this month look like the strongest open candidates yet: Qwen 3.6 35B-A3B (released April 15) and Gemma 4 26B (released April 2). Time to actually try them.

2. Hardware. MacBook Pro M4 Max, 14 cores, 36 GB unified memory. This is the author's machine for the run. If local models feel slow here, the day-to-day laptop experience is still going to be rough for a lot of developers.

3. The Models.
   - Qwen 3.6 35B-A3B-coding-nvfp4: 21 GB on disk. MoE with 35B total parameters, only 3B active per token. Apache 2.0. Vendor-reported SWE-Bench Verified 73.4 in Qwen's own agent scaffold.
   - Gemma 4 26B: 17 GB on disk. MoE with 25.2B total parameters, 3.8B active per token. Apache 2.0. Native function calling and vision baked in.

4. The Setup. Ollama since v0.14.0 (January 2026) exposes an Anthropic-compatible Messages API. Claude Code talks to it directly with ANTHROPIC_BASE_URL=http://localhost:11434 and ANTHROPIC_AUTH_TOKEN=ollama. Ollama also ships an `ollama launch claude --model <name>` shortcut.

5. The Auth Gotcha. If you have Claude Code logged into your real Anthropic account, the keychain credentials win over the env vars and requests still bill against your account (the banner shows "API Usage Billing"). The fix without nuking your global login is `claude --bare` mode, which skips keychain reads and uses ANTHROPIC_API_KEY for auth. Worth its own callout.

6. The Test. One trivial question, asked of Claude Code in the gigi-zone repo:
   "what's this project about in 100 words or less"

   Four contestants:
   - Claude Code + Opus 4.7 (cloud, Anthropic)
   - OpenAI Codex (cloud, default model)
   - Claude Code + Qwen 3.6 35B-A3B (local, via Ollama)
   - Claude Code + Gemma 4 26B (local, via Ollama)

7. The Results.
   - Claude Code + Opus 4.7: 2-3 seconds. Stayed under 100 words.
   - Codex: 2-3 seconds. Stayed under 100 words.
   - Qwen 3.6 (local): 1 minute 13 seconds.
   - Gemma 4 (local): 1 minute 52 seconds. Generated 199 words. Ignored the explicit constraint.

8. Why So Slow. Three reasons worth naming, briefly:
   - First-token latency. Claude Code packs a big system prompt plus repo context into every turn. The model has to chew through all of that before it emits a single token. On a 36 GB Mac that's seconds of pure prefill.
   - No prompt caching. Anthropic's hosted models cache the system prompt. Ollama's Anthropic-compat surface does not. Every turn pays the full prefill cost.
   - MoE doesn't help disk or RAM. The 3B-active part makes generation faster once it starts, but all 25-35B weights still have to sit in unified memory next to whatever else is running.

9. The Verdict. The local-models story for my everyday agentic coding workflow is "not yet, even with the new MoE releases on good laptop hardware." Two minutes for a 100-word project summary is unusable for that workflow. The cloud frontier models aren't just better at reasoning, they're also dramatically faster on simple turns thanks to massive backend infrastructure and prompt caching. For privacy-mandated or offline workflows it's good that local is now possible. For everyday use, this run was still too slow to feel practical.

10. Honest Caveats.
    - This is one trivial prompt, not a benchmark. The numbers will move with longer turns, with caching landing in Ollama, with smaller models, with quantization tweaks.
    - The constraint-ignoring behavior from Gemma 4 is a single observation, not a verdict on instruction following.
    - Performance will likely improve fast. This article is a snapshot of late April 2026.

Series format: CCDD series structure (emoji-bookend H2 headers, hook + bolded quote opening, series index link, What's Next, Take Home Points, book plug, Greek closing greeting).

Images:
- hero.png: The four contestants lined up at a starting line. Two big cloud server racks (labeled Opus 4.7 and Codex) on one side, two laptops (labeled Qwen 3.6 and Gemma 4) on the other. The laptops are obviously straining: smoke, fans visible. The server racks look bored. xkcd style.
- diagram-timings.png: A simple horizontal bar chart of the four timings. Opus 4.7 and Codex as tiny bars (2-3 sec). Qwen 3.6 a long bar (73 sec). Gemma 4 the longest bar (112 sec) with a small "199 words" annotation. Not a markdown table, an actual image.

Section outline:

1. Hook + bolded quote + <!--more--> + hero.png
2. Series index note
3. ## 🦙 Why Local? 🦙 (the promise: privacy, cost, offline)
4. ## 🧠 The New Local Brains 🧠 (Qwen 3.6 and Gemma 4 intros)
5. ## 🔌 Wiring Claude Code to Ollama 🔌 (Anthropic API compat, env vars, --bare, auth gotcha)
6. ## ⚔️ The Showdown ⚔️ (the question, the four contestants)
7. ## 📊 The Results 📊 (the four timings, the Gemma 199-word miss, diagram-timings.png)
8. ## 🐌 Why So Slow? 🐌 (prefill, no prompt caching, MoE-RAM reality)
9. ## ⏭️ What's Next ⏭️
10. ## 🏠 Take Home Points 🏠
11. Book plug
12. Greek closing
