CCDD #15. Slug: cc-deep-dive-15-know-your-rivals.

Title: Claude Code Deep Dive - Know Your Rivals

The article compares the configuration/harness surface of five AI coding agents: Claude Code, OpenAI Codex, Gemini CLI, Amp (Sourcegraph), and OpenCode (anomalyco). The angle is NOT "which is best" or benchmark scores. It's a deep comparison of how each tool lets you customize, configure, and control the agent: project instructions, custom commands, hooks, MCP, subagents, skills, plugins, permissions, memory, settings layers, sandboxing, and parallel execution. The goal is to help readers understand the design philosophy behind each tool and make informed choices.

Series index: Single link to the Medium CCDD series list (https://medium.com/@the.gigi/list/claude-code-deep-dive-5f842373dcaa).

Key content points:

1. Framing: All five tools have converged on remarkably similar feature sets. They all have project instruction files, MCP support, subagents, memory, and layered settings. But the depth, philosophy, and maturity vary. This article maps the configuration surface of each tool across 12 dimensions.

2. The Contenders (brief intro of each):
   - Claude Code: Anthropic's CLI agent. The one we've been deep-diving for 14 articles.
   - Codex: OpenAI's open-source CLI agent (github.com/openai/codex). Uses AGENTS.md.
   - Gemini CLI: Google's open-source CLI agent (google-gemini/gemini-cli). Uses GEMINI.md.
   - Amp: Sourcegraph's coding agent (amp.dev). Uses AGENTS.md. VS Code extension + CLI.
   - OpenCode: Open-source CLI agent (opencode.ai, github.com/anomalyco/opencode). 142K stars. Uses AGENTS.md. Reads CLAUDE.md and .cursorrules for compatibility. Client/server architecture with desktop app.

3. The 12 Dimensions (this is the meat of the article). For each dimension, describe what each tool offers. Use flowing prose, not tables (tables don't render on Medium). Group into subsections:

   **Context Engineering** (what the agent knows):
   - Project instructions: Claude Code has CLAUDE.md (multi-level, user/project). Codex has AGENTS.md (walked from home to cwd, with overrides). Gemini CLI has GEMINI.md (supports @file imports). Amp has AGENTS.md (directory-scoped, injected after file reads). OpenCode has AGENTS.md plus reads CLAUDE.md/.cursorrules for cross-tool compatibility, and supports custom instruction paths via config.
   - Memory: All five have memory systems. Claude Code has auto-memory in a dedicated directory. Codex has a memories subsystem with extraction/consolidation models. Gemini CLI appends to GEMINI.md. Amp saves to global AGENTS.md. OpenCode uses AGENTS.md created via /init.

   **Customization** (extending the agent):
   - Custom commands/slash commands: Claude Code has user-defined slash commands and skills. Codex has 30+ built-in commands but no user-defined ones (skills instead). Gemini CLI has TOML-based custom commands with namespacing. Amp replaced slash commands with skills and a command palette. OpenCode has template-based custom commands in .opencode/commands/.
   - Skills/reusable prompts: All five have skills. Claude Code's are markdown files with frontmatter. Codex's are directories with SKILL.md + scripts. Gemini CLI bundles skills in extensions. Amp has lazily-loaded agent skills. OpenCode has SKILL.md files with YAML frontmatter, and notably scans Claude-compatible paths (.claude/skills/) too.
   - Hooks: Claude Code has pre/post tool hooks in settings.json. Codex has no real hooks (just notify + Starlark execution policies). Gemini CLI has 11 hook event types (the most comprehensive). Amp has hooks but minimal documentation. OpenCode: no hooks documented.
   - MCP: All five support MCP servers. This is the convergence point. Different config syntax but same protocol.
   - Plugins/extensions: Claude Code has a plugin marketplace. Codex has early plugin support. Gemini CLI has a full extension system with a gallery. Amp has no formal plugin system (MCP + toolbox instead). OpenCode has plugins from npm or .opencode/plugins/.

   **Agent Architecture** (how the agent delegates):
   - Subagents: Claude Code has subagents with worktree isolation + agent teams. Codex has multi-agent threads (max 6 concurrent) with /fork. Gemini CLI has built-in subagents (codebase_investigator, browser_agent, etc.) + custom agents. Amp has Task/Oracle/Finder/Handoff pattern. OpenCode has Build/Plan/General/Explore agents + custom agents defined in .opencode/agents/.
   - Parallel execution: Claude Code has worktrees + agent teams. Codex has multi-agent threads + fanout. Gemini CLI has experimental worktrees. Amp has concurrent Tasks + Handoff. OpenCode's General subagent supports parallel execution of multiple work units.

   **Safety & Control** (how the agent is constrained):
   - Permissions: Claude Code has allow/deny/ask rules with layered settings. Codex has four approval policies + Starlark rules + guardian subagent. Gemini CLI has four modes + Conseca (LLM security checker). Amp has pattern-matched permission rules + guarded files. OpenCode has allow/ask/deny per tool with glob patterns, agent-level overrides, and built-in doom_loop detection.
   - Sandboxing: Claude Code has process-level sandbox + Docker sandbox + devcontainers. Codex has OS-level sandbox (Seatbelt on macOS, Bubblewrap on Linux). Gemini CLI has the most options (Docker, Podman, LXC, macOS profiles, custom Dockerfiles). Amp has no sandbox (relies on permissions + secret redaction). OpenCode has snapshot-based change tracking but no container sandboxing.
   - Settings layers: Claude Code has user/project-shared/project-local/enterprise. Codex has user/project/profiles. Gemini CLI has system-defaults/user/project/system-overrides. Amp has user/workspace/enterprise. OpenCode has 8 layers (the most): remote org config, global, custom, project, .opencode dirs, inline, managed config, and macOS MDM.

4. The Pioneer Effect: Claude Code spearheaded much of the innovation here. CLAUDE.md established the pattern of project instruction files that the others adopted (AGENTS.md, GEMINI.md). Skills, MCP (Anthropic's own protocol), hooks, and subagents all appeared in Claude Code first and were then picked up by competitors. OpenCode makes this lineage explicit by reading CLAUDE.md and scanning .claude/skills/ paths directly. This isn't a knock on the others. Good ideas should spread. But it's worth acknowledging where the patterns originated. The competitive pressure has been healthy: Gemini CLI pushed hooks further (11 event types vs Claude Code's pre/post), Codex added Starlark execution policies for fine-grained control, Amp developed specialized subagent roles (Oracle/Finder/Librarian), and OpenCode stacked 8 config layers including MDM support.

5. Where They Diverge: Despite the shared foundation, each tool has a distinct philosophy.
   - Claude Code bets on plugins and agent teams (ecosystem + orchestration)
   - Codex bets on sandboxing and execution policies (safety-first, Starlark for fine-grained control)
   - Gemini CLI bets on extensions and hooks (maximum extensibility, full extension gallery)
   - Amp bets on subagent specialization (Oracle/Finder/Librarian pattern, each agent has a distinct role)
   - OpenCode bets on openness and compatibility (reads everyone's config files, 8 config layers, provider-agnostic, client/server architecture for future remote control)

6. What's Unique: Features that one tool has and others haven't adopted yet. Channels and computer use (Claude Code). Extension galleries (Gemini CLI). Guardian subagent for AI-driven approvals (Codex). Toolbox scripts-as-tools (Amp). Cross-tool config compatibility and LSP integration out of the box (OpenCode). These are today's differentiators, but given the cross-pollination trend, expect them to spread.

Series format: CCDD series structure (emoji-bookend H2 headers, hook+quote opening, series list link, What's Next, Take Home Points, book plug, closing greeting in Welsh).

Categories: Claude, ClaudeCode, AICoding, AIAgent, CodingAssistant, Codex, Gemini, Amp, OpenCode
Date: 2026-04-12

Images:
- hero.png: vibrant hero image showing five distinct AI agents (represented as distinct colored geometric figures) facing each other in an arena or ring, competitive but respectful
- diagram-convergence.png: xkcd-style diagram showing the 5 tools converging on the same feature set, with Claude Code at the origin point and arrows showing adoption
- diagram-12-dimensions.png: xkcd-style visual summary of the 12 dimensions showing relative depth per tool
