+++
title = 'Fixing the Open AI Tool Calling API'
date = 2024-08-04T12:51:52-07:00
+++

The design of the OpenAI tool calling API can cost you major bucks 💵. In this blog post I dive into
the nuances of tool calling and show how one brave library (simple-openai) fixed it for you.

<!--more-->

## How do Tools Work? 🛠️

Tools are a powerful feature of the
OpenAI [chat completions API](https://platform.openai.com/docs/api-reference/chat/create). They
allow you to inform the model that if it needs additional information to construct its answer it can
invoke some pre-defined tools and incorporate the tool responses into its context before responding
to the original prompt.

For example, consider an AI system designed to provide its users with travel information ✈️. A user
may ask a question like: "I want to fly from Rome to Rio tomorrow afternoon, but I don't want to
change plains more than once, also pay no more than $400. can I haz it?" 🍹☀️

LLMs being pre-trained models without access to an up-to-date flight information are unable to
provide a useful response. But, we (AKA the AI system developers) can help the model by augmenting
the request with tools! Here is a tool definition that can help:

```shell
get_flight_info(date, origin, destination)
```

Now, when the model receives the request it realizes that it needs to get recent flight information
and, it can utilize this convenient tool.

How does it work then? The model returns a response to the original query that includes
a `tool_calls` array that contains the tool name `get_flight_info`, the date of tomorrow, "Rome"
and "Rio". Then, the system is responsible for collecting the information by calling airline APIS or
maybe using some cached information. The system sends the data to the LLM, which can now scan the
info and find the flights that match the user requirements and generate the final response.

Note that the model may need to invoke multiple tools or the same tool multiple times in order to
collect all the data.

## The Tool Calling Design ⚙️

OK. We got the gist of how this thing works. Let's dive into the specifics. When you send a request
to the `/chat/completions` API you can provide a array of `tools` definitions and a `tool_choice`
parameter.

Here is an example of tool definition in Python that corresponds to our `get_flight_info`:

```python
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_flightinfo",
                "description": """Get the airline, flight number, departure and arrival times
                                  private and connections",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "The flight departure date",
                        },
                        "origin": {
                            "type": "string",
                            "description": "The city the flight departs from",
                        },
                        "destination": {
                            "type": "string",
                            "description": "The city the flight arrives at",
                        },                        
                    },
                    "required": ["date, "origin", "destination"],
                },
            },
        }
    ]
```

Remember, that multiple tools may be provided for a request.

Let's look at `tool_choice` now. This parameter lets you control how the model invokes the tools
from the array you provided. It can take several values

- **auto**: the model decides which tools if any to invoke
- **required**: the model must invoke at least one tool. The model decides which tool/s to invoke.
- **none**: the model must not invoke any tool
- **function** (with a name): the mode must invoke exactly the function tool with the provided name

This design is broken! 💔

## What's wrong with this API design? 🤷‍

First, it allows invalid combinations. For example, you can provide an empty array of tools with a
tool choice of `required` (or not pass an array of tools at all). Another invalid combination is
providing a tool choice of `function` with a function name that doesn't exist in the tools array.

It is also unnecessarily complex. There is no need for the tool choices of `none` and `function`. If
you don't want the model to invoke any tool, just don't provide a `tools` array (it's optional).
If you want the model to call a specific function, populate the `tools` array with that function
only and specify a tool choice of `required`.

OK. Who cares? so, the API is a little cumbersome. So what?

Great question!  👏

The issue is that this design promotes the bad practice of preparing an initial request object with
a big array of all the tools you may want the model to be able to call. Then, in your code when you
send different requests to the model that require different set of tools to be invoked you keep the
big array of tools and just modify the tool choice parameter.

Yeah, makes sense. Why would you want to mess with the array of tools for every request?

Another awesome question! 👏

The reason you want to avoid sending tools that you never want the model to invoke is money 💲! With
the chat completions API you send the full array of tools in each request. Even if you make tons of
requests with exactly the same set of tools, you still must send them each and every time. Now, you
can have up to 128 different tools in the current version of the OpenAI API. Each one of these tools
require a JSON blob with the function name and the parameter descriptions. This can bloat your
request size and egress is not free! But, worse than the network bandwidth this can add up
quickly to a LOT of tokens 🎟️!

Tokens are expansive! You shouldn't send useless tokens to the model that it doesn't need.

## What can we do about it? 🤔

First of all, I opened a GitHub issue on the openai-openapi repo (yes, it's a mouthful) that
explains the whole deal:
https://github.com/openai/openai-openapi/issues/259

That was almost 3 months ago. It wasn't assigned to anyone and there was no comment from any OpenAI
person. Maybe if you upvote, it has a better chance of someone considering it.

If you use Java to talk to LLMs then you're in luck
🍀.  [Sashir Estela](https://github.com/sashirestela) - the author
of [simple-openai](https://github.com/sashirestela/simple-openai) - picked up the issue and quickly
added special support for optimizing the tools array based on your tool choice.

So, if your tool choice is `none` the library will not send any tools to OpenAI even if your request
had tools. Also, if you specify a specific function only this function will be passed in the
tools array. This is great. You get to initialize your big array of tools once if you prefer it, and
the library makes sure you don't waste precious tokens and send tools that are not needed.

[simple-openai](https://github.com/sashirestela/simple-openai) in case you don't know is the best
OpenAI Java client library 🏆. I wrote a whole blog post about evaluating all the OpenAI client
libraries. Check it out if you're not convinced:

[In Search of the Best OpenAI Java Client](http://localhost:1313/gigi-zone/posts/2024/02/in-search-of-the-best-openai-java-client/)

If you don't use Java, then just be mindful. In your code make sure to trim the tools array of each
request according to the tool choice.

## What about the Assistants API? 🧑‍💼

If you're keeping up with the blistering pace of innovation then you're aware of
the [OpenAI assistants API](https://platform.openai.com/docs/api-reference/assistants/object). This
API also supports the concept of tools. When you create an assistant you can pass it a list of
tools. This is a different model where you provide the tools once when you create the assistant.
It's equivalent to always sending all the tools and a tool choice of `auto`. However, you can still
have granular control with override tools and tool choice at the thread and run levels if needed.

Like 👍, share 🔗 and subscribe 🔔!

just kidding 😜, the most you can do is star ⭐ and/or watch 👁️ the repo:

https://github.com/the-gigi/gigi-zone

Gigi, out 🎤⬇️
