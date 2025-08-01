# Blog post topics


## AI-6

Implement k8s-ai in Golang and/or rust and extend it ti support multiple tools including:


## Adding Gemini support to simple-openai











- kubectl 
- git
- OpenAI (higher-level models)
- cloud provider CLIs (aws, gcloud, az)

## Kubernetes Node Group Architecture

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

## Dockerize the World

https://github.com/the-gigi/docker-images


## AppleScript vs. JXA


## OpenAI JavaClient library

https://github.com/the-gigi/llm-playground-java/

## Prompt Engineering (the old kind)

https://github.com/the-gigi/dotfiles/blob/master/components/prompt.sh

https://github.com/the-gigi/dotfiles/blob/master/rcfiles/.p10k.zsh

## The CLI is an API

- kubectl
- aws
- gcloud
- az
- psql

## Fuzz-Emoji - Polyglot Fun

- Python
- Golang
- Rust

## Free as in Tier

Fuzz-emoji in the cloud

- AWS Lambda
- Google Cloud Functions
- Azure Functions

## Knative functions

Fuzz-emoji in Kubernetes

## Python f-strings

Explore the recent innovations like comments, str(), repr() and ascii() and async
https://docs.python.org/3/reference/lexical_analysis.html#f-strings

Compare to other languages

| Language      | Equivalent to Python f-string                                | Syntax Example                                    | Example Output           |
|---------------|--------------------------------------------------------------|--------------------------------------------------|--------------------------|
| **C/C++**     | `sprintf` or `std::format` (C++20)                           | `std::format("Hello, {}!", name);`               | `Hello, Gigi!`           |
| **Java**      | `String.format`                                              | `String.format("Hello, %s!", name);`             | `Hello, Gigi!`           |
| **JavaScript/TypeScript** | Template literals                                | `` `Hello, ${name}!` ``                          | `Hello, Gigi!`           |
| **Go**        | `fmt.Sprintf`                                                | `fmt.Sprintf("Hello, %s!", name)`                | `Hello, Gigi!`           |
| **Rust**      | `format!` macro                                              | `format!("Hello, {}!", name);`                   | `Hello, Gigi!`           |
| **Ruby**      | String interpolation with `#{}`                              | `"Hello, #{name}!"`                              | `Hello, Gigi!`           |
| **C#**        | String interpolation with `$`                                | `$"Hello, {name}!"`                              | `Hello, Gigi!`           |