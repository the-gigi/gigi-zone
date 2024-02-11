+++
title = 'In Search of the Best OpenAI Java Client'
date = 2024-02-03T15:31:17-08:00
+++


Alright. This is going to be a long one. We're going on a wild hunt for
the BEST Java library to talk to OpenAI
API-compatible services!

<!--more-->

Code is available upon request... or just clone:

https://github.com/the-gigi/llm-playground-java

Everybody and their sister is going crazy about the amazing abilities of
large language models. At the moment OpenAI leads  the pack in terms 
of performance and recognition (mostly thanks to ChatGPT). But, a lot of
work is done across the board by the open source community, commercial
companies and of course the big cloud providers.

I wanted to test another LLM provider - [Anyscale](https://www.anyscale.com). Anyscale is 
mostly known for providing a general-purpose AI platform based
on [Ray](https://docs.ray.io/en/latest/), but they also provide an Endpoints service that hosts
various open-source LLM foundation models.

See https://www.anyscale.com/endpoints.

The codebase I was targeting uses the [openai-java](https://github.com/TheoKanning/openai-java) library to
access the OpenAI service. One of the main requirements was to evaluate
if Anyscale supports function calling, which is a super-cool feature 
where you can extend the capabilities of the LLM by letting it call 
functions in your code and incorporate the response into its context.

Alright, I checked the docs and the code for **openai-java** and quickly
discovered that it hard-codes the base URL of the OpenAI service. 
Unfortunately, it wasn't designed for easy extension or configuration.

I decided to start a little standalone project to play with different
providers and evaluate them as well as make the necessary changes to 
make openai-java work with Anyscale. For starters, I wrote a little 
wrapper and combined some of the low-level components to create
a [client that can accept any base URL](https://github.com/the-gigi/llm-playground-java/blob/main/src/main/java/com/github/the_gigi/llm/client/OpenAiJavaClientBuilder.java#L44).

### 🤔 Evaluate Anyscale using openai-java 🤔

Cool. I was able to connect successfully to Anyscale, send it questions
and get answers through the chat completion endpoint 😎. However, when
I tried to add functions things fell apart.

It turns out that **openai-java** is using a [deprecated format](https://platform.openai.com/docs/api-reference/chat/create#chat-create-function_call) 
for function calling.

OpenAI still supports the deprecated syntax, so **openai-java** can do
function calling against it. However, the Anyscale Endpoints service 
apparently supports only the modern syntax. Here is what a request with
functions looks like from **openai-java**

```
Authorization: Bearer dummy
Content-Type: application/json; charset=UTF-8
Content-Length: 571
Host: localhost:5000
Connection: Keep-Alive
Accept-Encoding: gzip
User-Agent: okhttp/4.10.0

{'function_call': 'auto',
 'functions': [
    {'description': 'Get work history employees of a company',
        'name': 'get_work_history',
        'parameters': {
            '$schema': 'http://json-schema.org/draft-04/schema#',
               'additionalProperties': False,
               'properties': {'name': {'description': 'Name of '
                                                      'company, '
                                                      'for '
                                                      'example: '
                                                      "'Microsoft' "
                                                      'or '
                                                      "'Netflix",
                                       'type': 'string'}},
               'required': ['name'],
               'title': 'Company Info Request',
               'type': 'object'}}],
 'max_tokens': 100,
 'messages': [{'content': "what's microsoft employee work history?",
               'role': 'user'}],
 'model': 'mistralai/Mixtral-8x7B-Instruct-v0.1',
 'n': 1,
 'temperature': 0.9}

127.0.0.1 - - [24/Jan/2024 10:07:57] 
"POST /v1/chat/completions HTTP/1.1" 200 -
```

Note the deprecated  `function_call` and `functions` fields.

The official [openai](https://github.com/openai/openai-python) Python
library uses the new format of `tools` and `tool_choice`:

```
Host: localhost:5000
Accept-Encoding: gzip, deflate
Connection: keep-alive
Accept: application/json
Content-Type: application/json
User-Agent: OpenAI/Python 1.9.0
X-Stainless-Lang: python
X-Stainless-Package-Version: 1.9.0
X-Stainless-Os: MacOS
X-Stainless-Arch: arm64
X-Stainless-Runtime: CPython
X-Stainless-Runtime-Version: 3.11.7
Authorization: Bearer dummy
X-Stainless-Async: false
Content-Length: 593
{'messages': [
    {'content': 'You are helpful assistant.', 'role': 'system'},
    {'content': "What's the weather like in San Francisco?",
               'role': 'user'}],
 'model': 'mistralai/Mixtral-8x7B-Instruct-v0.1',
 'tool_choice': 'auto',
 'tools': [
    {'function': {
        'description': 'Get the current weather in a given '
                       'location',
```

It works with both OpenAI and Anyscale.

### 👀 Looking into openai-java 👀

Alright, let's check under the hood. Maybe, this can be resolved.
Unfortunately, I discovered that openai-java is not actively
maintained. [Theo Kanning](https://github.com/TheoKanning) - the
author/maintainer seems to have very limited bandwidth.

There are multiple significant open issues and PRs waiting. The
maintainer doesn't engage in discussions or threads. There is an issue
from June 2023 specifically asking if the project is still maintained:

https://github.com/TheoKanning/openai-java/issues/301

The maintainer said that the project has gotten too big, and he’ll think
about involving other people. That didn't seem
to happen so far.

In addition to the deprecated function calling issue, there is no
support for parallel function calling nor the new JSON format 
(there are unmerged PRs to address these)

Finally, the client has dependency with a known vulnerability

Overall, the library doesn't seem like a solid foundation to build on.
It is risky to keep using it even for accessing OpenAI, and it is a 
blocker for accessing Anyscale.

### ⚖️ Weighing the Alternatives ⚖️

Alright, we can't use openai-java as is or wait for it to address the
issues. Here are a few alternatives:

- Fork openai-java and take of business ourselves
- Use the official Python openai library from Java
- Build our own Java client library from scratch
- Use another Java library

I won't go into the pros and cons of each option and just say that
searching for another library can be done quickly, and if a good one 
is found then it beats all the other alternatives (which are still there
if no good library can be found).

So, without further ado let's explore the space of OpenAI Java.

### 🔍 Surveying the  Terrain 🔍

Cool. We have a direction let's find us some OpenAI Java client
libraries. The first step was checking out the OpenAI website, to look
for recommendations. OpenAI provide two official client libraries for
Python and Javascript/Typescript. They also mention the Azure OpenAI 
client libraries that are compatible with both OpenAI and Azure OpenAI. 
Then, there are community libraries. Guess what? The only reference to
a Java library is our very open openai-java.
See https://platform.openai.com/docs/libraries/java

OK. No problem. Let's do an internet search...

All kind of libraries come up. Based on a quick look into each one based
on popularity, activity and overall impression I picked a few candidates
to look into:

- [openai-kotlin](https://github.com/Aallam/openai-kotlin)
- [langchain4j](https://github.com/langchain4j/langchain4j)
- [simple-openai](https://github.com/sashirestela/simple-openai)

Let's see how they did and who came on top!

### 💜 openai-kotlin 💜

Kotlin is not Java! but, it's close enough :-) I never wrote a single
line of Kotlin before or even looked at the language. Actually, before
this project I haven't written any Java code for 18 years and even back
then it was only a few months. So, obviously as I am brushing up on my
rusty Java skills the best move is to throw a whole new language
into the mix. I'm excited!

Kotlin was easy to pick up and I learned the hard way some of the
intricacies of its Java integration. Theoretically,
you can just drop some Kotlin into your Java project and vice versa. In
practice there are some rough edges. But, overall it was pretty smooth.
At this point I had a LLMClient interface:

```
public interface LLMClient {
  String complete(String prompt);
  String complete(CompletionRequest completionRequest);
  List<String> listModels();
}
```

The interface exposes just the capabilities I need at the moment, 
but can be extended of course. I also had two concrete implementations 
based on openai-java and openai-kotlin. The openai-kotlin library 
supports the new format of tools.

Unfortunately, it has a serialization issue due to incorrect metadata
for tool functions. Simple chat completion works, but completion with 
tools fails. Again, it works with OpenAI, which is probably more 
forgiving and ignoring the incorrect metadata. I opened an [issue](https://github.com/aallam/openai-kotlin/issues/301) 🐞.
Ha! as I'm writing this, I checked the issue again. It was fixed just a
few hours ago. How cool is that?

There is no new release yet, so I'll have to wait before testing it.
I'll keep you posted...

Let's move on to another library.

### 🦜 langchain4j 🦜

The [langchain4j](https://github.com/langchain4j) is a large with a 
massive scope to integrate AI and LLM capabilities into Java 
applications. It is inspired by the well-known [langchain](https://github.com/langchain-ai/langchain)
project as well as [Heystack](https://github.com/deepset-ai/haystack) and 
[LlamaIndex](https://github.com/run-llama/llama_index).

It has a unique approach where it introduces a magical abstraction
called an AI Service, which is just a plain interface. You define 
an interface, and Langchain4J figures out what you want. For chat
completion functionality, it is as simple as:

```
/**
 * Interface defining the assistant's chat functionality.
 */
interface Assistant {
  /**
   * Handles chat interactions.
   *
   * @param userMessage The message from the user.
   * @return The response from the assistant.
   */
  String chat(String userMessage);
}
```

Then, You create a client that can talk to an OpenAI provider and  
instantiate an assistant (with tools if you want):

```
    var client = OpenAiChatModel.builder()
        .apiKey(apiKey)
        .baseUrl(baseUrl)
        .modelName(model)
        .build();

    this.defaultAssistant = AiServices.builder(Assistant.class)
        .chatLanguageModel(client)
        .tools(tools)
        .chatMemory(MessageWindowChatMemory.withMaxMessages(10))
        .build();
```

That's all. Now, to have the assistant perform chat completions 
including function calls, you just call the assistant's
`chat()` method with your prompt.

```
  @Override
  public String complete(String prompt) {
    return this.defaultAssistant.chat(prompt);
  }
```

This is all super awesome. But, then we start to drill down and look
under the cover we discover that Langchain4J uses yet another Java
library - [openai4j](https://github.com/ai-for-java/openai4j) - to do
the heavy lifting of implementing the OpenAI API and talking to LLM
provider. Now, openai4j doesn't implement the OpenAI API fully. It does
implement proper function calling with newer tool format, but it lacks
other important features. The developers don't seem to be very 
responsive. There are several issues that open for months. So, 
Langchain4j on top of openai4j fulfills the current criteria of 
supporting chat completion with function calling on both OpenAI and 
Anyscale. But, there are some warning signals ⚠️.

Let's check out our last contender...

### 💎 simple-openai 💎

The [simple-openai](https://github.com/sashirestela/simple-openai)
library is a hidden gem. It is literally hidden! I have no idea how I
stumbled on it. I think I saw it mentioned in some Reddit thread, but I 
can't locate it anymore. If you run a search on "OpenAI java client" or 
similar variations it just doesn't come up. Anyway, simple-openai is
[simply the best, better than all the rest](https://www.facebook.com/TinaTurner/videos/2423149307953757/).

The library fully implements the complete OpenAI API including the new
assistant API, JSON response format and of course it supports the new
tool format for function calling. I was able to utilize it to access 
Anyscale with no problems whatsoever. When I checked it out I was 
pleasantly surprised to see that the code is super-clean and elegant.

I am perplexed as to why such a high-quality library is not more
visible. I hope to help with this blog post. I discussed it with the
[Sashir Estela](https://github.com/sashirestela) - the author - who is 
very motivated, responsive and interested in promoting open-simpleai and 
making it available to more engineers.

### Final words

My journey into the world of large language models has just begun. There
is a lot to learn and things change and evolve at neck-breaking speed 
(Bard just became Gemini. did ya know?). I'll be back with more cool 
stuff. Stay tuned...

Oh, before you leave... go to [simple-openai](https://github.com/sashirestela/simple-openai) and
show it some love (AKA GitHub stars ⭐).
