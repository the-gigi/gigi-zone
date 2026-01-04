+++
title = 'Claude Code Deep Dive - Basics'
date = 2026-01-04T21:54:12-08:00
categories = ["Claude", "ClaudeCode",  "AICoding", "AIAgent", "CodingAssistant"]
+++

In [Confessions of an ex-coder](https://medium.com/@the.gigi/confessions-of-an-ex-coder-5122106f2327) I shared my workflow and how I let Claude Code do all the heavy lifting for me. It was super rewarding and productive, but I have used it at a very basic level. I promised to study it more deeply. This is it! 

My way for studying anything is experimenting/building something and then writing about it. This is the first article in the *CCDD* (Claude Code Deep Dive) series.

I'll cover some general and personal background and history of AI coding and then show some basic yet useful Claude Code tips.

**“AI will soon be writing 90 percent of all code.” - Dario Amodei, Anthropic CEO, March 10 2025**

<!--more-->

![](images/hero.png)

## 🗺️ Where are We? 🗺️

Humans shouldn't code professionally anymore. Period. LLMs are in general better and waaaaaay faster. I won't debate this, and you can save your counter examples. If you're an AI non-believer that's totally cool. Just wait and see.

Humans will continue to code professionally for many years due to a variety of reasons, but not because humans are better. Of course, LLMs keep improving faster and faster, but they are already superior to top-notch professional software engineers. Humans still have a role as software architects and reviewers (I won't speculate for how long in this post).

Personally, I haven't written any code or configuration for several months. Same with the rest of my team. The productivity benefits are off the charts.  Now, the question is how do you use AI to help you produce software.

## 📜 Brief History of AI coding 📜

In the olden days we had Github Copilot in our IDE, and it could suggest and generate some code for us. Also, ChatGPT could generate lots of code you could paste into your
project. At this stage, I have used it as a glorified autocomplete and to generate massive amounts unit tests. Soon
after, AI-first code editors like Cursor and Windsurf started to dominate the conversation, more recently Google launched Antgravity. I must admit that I skipped
this phase completely. I jumped right ahead to the AI coding agent.

This is a whole different mode of software development. You talk with your AI coding agent, and it does the work. You're now a manager of one or more virtual software engineers. Check out my original article [Managing software engineers in the AI era](https://medium.com/@the.gigi/managing-software-engineers-in-the-ai-era-18ac7f003a1d) 

Let's see why I chose Claude Code.

## ⭐ Why Claude Code? ⭐

There are a bunch of AI coding agents besides [Claude Code](https://code.claude.com) like OpenAI Codex, Gemini CLI, SourceGraph Amp and many more. I believe Claude Code is ahead of the pack in terms of user experience, configuration and control as well as the default experience. This seems to be the consensus from what I read. I have played with codex and amp a little bit, so it's not all hearsay. Anthropic seems to really focus on building the best AI software engineer and it shows.

Alright, let's get hands on. There are many ways to run Claude Code. I'll focus on running in the terminal and in your IDE and mention a few other ways.

## 💻 Claude Code in the Terminal 💻

Claude Code is basically a super fancy CLI. It does a lot of magic with dynamic refreshing, status updates, syntax highlighting and all sorts of terminal wizardry. But all that magic comes at a cost. The [infamous flickering bug](https://github.com/anthropics/claude-code/issues/769#issuecomment-3667315590) is where you feel it the most as a user. Anthropic has been working on it for months and made progress, but I still run into it from time to time as of January 2nd 2026.

I use it with iTerm2 on Mac. The main thing to know upfront is how to type multi-line text. Just hitting `return` or `enter` sends your text to Claude immediately. In iTerm2 you type `shift + return` to start a new line. This is crucial when you want to provide detailed instructions or paste code.

You may need to run the `/terminal-setup` slash command once to make everything work smoothly.

### Permissions

Claude will constantly ask you for permissions before doing anything. You can be as permissive or restrictive as you like. We'll talk about configuring fine-grained permissions some other time. I personally go with full permissions because I trust Claude and I want speed. Your mileage may vary.

I have an alias set up:

```bash
cl='claude --dangerously-skip-permissions'
```

This flag allows Claude Code to do anything you can do (well, the OS user you started Claude Code with).

### Resuming Sessions

Claude Code keeps track of all your previous sessions, which is super handy. You can resume the very last session with:

```bash
cl --continue
```

I have an alias for this too:

```bash
alias clc='cl --continue'
```

This is my primary resume mode when something goes wrong at the terminal level. This is usually the [infamous flickering bug](https://github.com/anthropics/claude-code/issues/769), which Anthropic is working on for months! 

So, when I want to reset the terminal session and continue where I left off I just kill the terminal session with a couple of `ctrl+C`s and type `clc`.

If you want to resume another previous session you can type:

```bash
cl --resume
```

You can also use the `/resume` slash command within Claude Code. Both will give you a list of previous sessions to choose from.

### Shortcuts

Claude Code has several keyboard shortcuts that control how it works. Type `?` to see all of them 

```
  ! for bash mode       double tap esc to clear input      ctrl + _ to undo
  / for commands        shift + tab to auto-accept edits   ctrl + z to suspend
  @ for file paths      ctrl + o for verbose output        ctrl + v to paste images
  & for background      ctrl + t to show todos             opt + p to switch model
                        shift + ⏎ for newline              ctrl + s to stash prompt
```

Note that `shift+tab` cycles through the permissions modes, so `auto-accept edits` is displayed just because currently I'm in the `bypass permissions` mode. There is one more permission mode `plan`, in which Claude Code will discuss and plan, but will not make changes to your files.

Let's discuss a couple of the other shortcuts

### Slash Commands

Claude Code has a bunch of slash commands for various operations. Just type `/` and you'll see a list of available commands. The `/terminal-setup` I mentioned earlier is one of them. We'll cover slash commands in depth in a future article in the series.

### Quick Shell Commands

You can quickly run shell commands with the `!` modifier. For example, `! pwd` will run the `pwd` command and insert the output right into the conversation. Super handy for showing Claude your current directory or the output of any command.

## 🛠️ Claude Code in the IDE 🛠️

Claude Code has plugins/extensions for different IDEs. I'm a JetBrains die-hard (sorry VS Code and its progeny). I use mostly PyCharm, Goland and RustRover.

JetBrains IDEs provide a built-in terminal, and you can just type `claude` in that terminal window. But here's the catch - `shift+return` for multi-line input may not work for you. You have a few options:

- Type `\+return`
- Type `ctrl+j`
- Install the Claude Code plugin and use `option+return`

Note that `option+return` doesn't work in RustRover even after installing the plugin. It seems to be buggy in general and sometimes complains that Claude Code is not installed. ¯\\\_(ツ)_/¯.

The plugin by default runs simply the command `claude`, which means it will annoyingly ask you for permissions all the time. But you can customize the command and add the `--dangerously-skip-permissions` flag if you want to skip that.

Everything I said about the terminal - resuming sessions, slash commands, quick shell commands - all works the same way in the IDE terminal.

## 🌐 Other ways to run Claude Code 🌐

There are several other ways to use Claude Code beyond the terminal and IDE. I don't really use them at the moment, but they're worth knowing about:

- **Claude Code on the Web** - run it in your browser
- **Claude Code Desktop** - standalone desktop application
- **Claude Code in Slack** - integrate it with your Slack workspace
- **Claude Code GitHub Actions** - automate workflows in GitHub
- **Claude Code in Chrome** - browser extension

I'm sticking with the terminal/IDE workflow for now since that's where I spend my time anyway. But depending on your workflow, one of these other options might be perfect for you. I'll explore some of them later.

## ⏭️ What's Next ⏭️

Just to give you a sense of how vast the Claude Code universe is and how much more you can do here are some topics I plan to over (not necessarily in this order):

- Configuration (CLAUDE.md and friends)
- Slash Commands
- MCP support
- Skills
- Subagents
- Hooks
- Plugins
- Additional ways to run Claude (including programmatically)
- Comparison with other AI coding agents

## 🏠 Take Home Points 🏠

- Programming has changed forever
- Adapt or become obsolete
- Claude Code provides the best user experience in January 2026
- Invest the time to study it deeply

🇨🇿 Na shledanou, moji přátelé! 🇨🇿
