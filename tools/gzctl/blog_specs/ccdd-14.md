CCDD #14. Slug: cc-deep-dive-14-strength-in-numbers.

Title: Claude Code Deep Dive - Strength in Numbers

The article covers running multiple Claude Code sessions in parallel: worktrees, fan-out patterns, agent teams, and practical orchestration strategies. This is the natural progression from article #6 (Subagents in Action), which covered delegation within a single session. Now we go multi-session.

Series index change: Starting with this article, replace the numbered list of previous articles with a single link to the Medium CCDD series list (https://medium.com/@the.gigi/list/claude-code-deep-dive-5f842373dcaa). Mention briefly that the list of previous articles has grown too large to include individually, so we're switching to a curated series list going forward.

Key content points:

1. The Problem: A single Claude Code session is powerful but sequential. Complex projects have independent workstreams that could run simultaneously. You're leaving cycles on the table. Article #6 covered subagents (delegation within a single session). This article goes bigger: multiple full Claude Code sessions working as a coordinated team.

2. The Building Blocks (brief, since the demo is the main event):
   - Git worktrees: `claude -w <name>` gives each session an isolated branch and directory. Auto-cleanup when done. `.worktreeinclude` for copying gitignored files.
   - Tmux integration: `claude -w <name> --tmux` for side-by-side visibility.
   - Subagent isolation: `isolation: worktree` in subagent frontmatter (connect back to article #6).
   - These are the primitives. Agent teams orchestrate them.

3. Agent Teams: The main feature. Enabled via `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. Architecture: one lead session that you talk to, which spawns teammates (each in its own context window and worktree). The lead plans the work, assigns tasks, teammates execute in parallel, inter-agent messaging for coordination when needed. Display modes: auto, in-process, tmux. This is the orchestration layer on top of the primitives.

   The critical difference from subagents (article #6): each teammate is a full interactive Claude Code session. You can switch to any tmux pane and talk to that agent directly: ask it questions, give it corrections, redirect its approach, or take over entirely. Subagents are fire-and-forget black boxes that return a result. Teammates are peers you can collaborate with. This makes agent teams fundamentally more powerful for real work where things don't go perfectly on the first try.

4. The Demo - CronJob Monitor (this is the centerpiece of the article): Build a Kubernetes CronJob Monitor from scratch by describing the project to the lead agent and letting the team build it in parallel. Walk through the entire experience from the user's perspective.

   The project: A Go service using client-go that runs in-cluster, lists CronJobs, and exposes a web UI (Go html/template) for viewing status, last execution, pause/resume, and manual trigger. Uses ServiceAccount + RBAC. Local dev via kind + Tilt. CI/CD via GitHub Actions.

   The point is NOT the finished app. It's showing the agent team workflow from the user's perspective:
   - Setting up the repo and enabling agent teams
   - Describing the project to the lead agent in a single prompt
   - Watching the lead decompose it into 4 workstreams (app, ui, cicd, local-env)
   - Watching teammates spin up in tmux panes, each in its own worktree
   - Observing inter-agent coordination (e.g., UI agent needs to know the API routes the app agent is building)
   - The lead merging branches when teammates finish
   - Narrate the experience: what went well, what was messy, where the lead made good/bad decomposition choices, how coordination worked in practice

   We build the project for real (throwaway local repo, no GitHub push). The project is complex enough to justify 4 parallel agents. The article focuses on the process: how the team coordinates, what decisions the lead makes, and what the experience feels like, rather than walking through the code itself.

5. Lessons and Practical Tips: Drawn from the demo experience. Context isolation (each agent has its own window, no shared memory). Merge conflicts and how to split work to avoid them. When NOT to parallelize (tightly coupled changes, small tasks). Cost/rate limit awareness.

Series format: CCDD series structure (emoji-wrapped H2 headers, hook+quote opening, series list link, What's Next, Take Home Points, book plug, closing greeting in Finnish).

Categories: Claude, ClaudeCode, AICoding, AIAgent, CodingAssistant, Parallelism
Date: 2026-04-05

Images:
- hero.png: vibrant hero image showing multiple Claude Code terminals working in parallel, conveying teamwork and speed
- diagram-agent-teams.png: xkcd-style diagram showing the agent teams architecture (lead + teammates, worktrees, inter-agent messaging)
- diagram-4-worktrees.png: xkcd-style diagram showing the 4 worktrees (app, ui, cicd, local-env) branching from main and merging back
- screenshot-tmux-4-panes.png: screenshot of tmux with 4 panes, each running a Claude Code worktree session
- screenshot-cronjob-ui.png: screenshot of the CronJob Monitor web UI (if the app actually works at the end, otherwise skip)
