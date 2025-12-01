# Blog post topics

## Python concurrency

- asyncio
- threading
- multiprocessing
- concurrent.futures
- concurrent.interpreters

## Python-ish languages

- Cython
- PyPy
- Mojo
- Interoperability with CPython
- honorable mention - Nuitka

## AI-6

Implement k8s-ai in Golang and/or rust with only MCP support.

## Confessions of an ex-coder

I used to be a coder. Every day I would pop up my IDEs (yes, plural) and happily bust some code. Life was good. But,
then AI arrived and quickly improved. First, it was just a little bit fancy code completion. I'll ask the AI to do
something little bit more complicated and it would fail hilariously. Then, it got better and better. 

## Kubernetes Node Group Architecture

## Kubernetes Blazing Fast Pods - Placeholder pattern

## Kubernetes Blazing Fast Pods - Idle Pool pattern

## Kubernetes Leader Election

## Kubernetes Resource Fine-tuning

## Configuration Files Considered Harmful (Sort of)

There is nothing like a good "<Blank> is considered Harmful" essay to exasperate the unwashed masses of anguished
software engineers toiling over their keyboards.

????

- Using direct Programming language structures
- Embedding configuration
- Hybrid (overrides)
- Dynamic configuration
- Env vars and command-line args

- Dishonorable mention - JSON as config

When config files shine.

## Mastering Docker

- Small images
- Minimal layers
- CMD and/or ENTRYPOINT
- shell vs. exec

https://www.docker.com/blog/docker-best-practices-choosing-between-run-cmd-and-entrypoint

## AppleScript vs. JXA

## Prompt Engineering (the old kind)

https://github.com/the-gigi/dotfiles/blob/master/components/prompt.sh

https://github.com/the-gigi/dotfiles/blob/master/rcfiles/.p10k.zsh

## The CLI is the API

Especially for AI agents

- kubectl
- aws
- gcloud
- az
- psql

## Fuzz-Emoji - Polyglot Fun

- Python
- Golang
- Rust

## Fuzz-emoji in the cloud

- AWS Lambda
- Google Cloud Functions
- Azure Functions

## Knative functions

Fuzz-emoji in Kubernetes

## Free as in Tier

- https://cloud.google.com/free/docs/free-cloud-features#free-tier
-

## Python f-strings

Explore the recent innovations like comments, str(), repr() and ascii() and async
https://docs.python.org/3/reference/lexical_analysis.html#f-strings

Compare to other languages

| Language                  | Equivalent to Python f-string      | Syntax Example                       | Example Output |
|---------------------------|------------------------------------|--------------------------------------|----------------|
| **C/C++**                 | `sprintf` or `std::format` (C++20) | `std::format("Hello, {}!", name);`   | `Hello, Gigi!` |
| **Java**                  | `String.format`                    | `String.format("Hello, %s!", name);` | `Hello, Gigi!` |
| **JavaScript/TypeScript** | Template literals                  | `` `Hello, ${name}!` ``              | `Hello, Gigi!` |
| **Go**                    | `fmt.Sprintf`                      | `fmt.Sprintf("Hello, %s!", name)`    | `Hello, Gigi!` |
| **Rust**                  | `format!` macro                    | `format!("Hello, {}!", name);`       | `Hello, Gigi!` |
| **Ruby**                  | String interpolation with `#{}`    | `"Hello, #{name}!"`                  | `Hello, Gigi!` |
| **C#**                    | String interpolation with `$`      | `$"Hello, {name}!"`                  | `Hello, Gigi!` |
