+++
title = '🤖 AI Agents are not Real'
date = 2025-05-11T21:54:12-08:00
categories = ["AI"]
+++

AI agents are all the rage these days. They’re the new shiny ✨ toy that everyone wants to play with 🧸.
There’s only one small problem: they’re not real 👻. Yes, you heard me right 👂. AI agents are just a figment of our AI
frameworks 🛠️ — really just an anthropomorphism 🧍‍♂️ of a very useful pattern for interacting with LLMs.

**“The question of whether a computer can think is no more interesting than the question of whether a submarine can
swim.” ~ Edsger W. Dijkstra**

<!--more-->

![](images/hero.png)


## 🧠 What is an AI agent? 🧠

There are many definitions of AI agents. Here is what ChatGPT said when I asked it to tell me what an AI agent is in 4
bullet points:

- 🤖 **Autonomous:** Acts independently to pursue goals without continuous human input.
- 👁️ **Perceptive:** Observes and interprets its environment via data, APIs, or sensors.
- 🧠 **Reasoning & Planning:** Makes decisions and plans actions to achieve objectives.
- ⚙️ **Action-Oriented:** Executes tasks using tools, APIs, or system commands to impact the environment.

That sounds about right and aligns with most people's understanding of AI agents. I'm here to show you there is no such
autonomous, perceptive, reasoning and action-oriented entity. It's all smoke and mirrors 💠.

## ☸️ The Kubernetes AI "agent" ☸️

Let's have some fun with Kubernetes and an AI "agent". Here's the plan: we will create a local Kubernetes cluster, cause
some mayhem and then let the AI "agent" diagnose and fix the problem. First, let's create a
local [KinD](https://kind.sigs.k8s.io) cluster:

```
❯ kind create cluster -n k8s-ai
Creating cluster "k8s-ai" ...
 ✓ Ensuring node image (kindest/node:v1.33.1) 🖼
 ✓ Preparing nodes 📦
 ✓ Writing configuration 📜
 ✓ Starting control-plane 🕹️
 ✓ Installing CNI 🔌
 ✓ Installing StorageClass 💾
Set kubectl context to "kind-k8s-ai"
You can now use your cluster with:

kubectl cluster-info --context kind-k8s-ai

Have a nice day! 👋

```

Now, let's cause some trouble in the cluster. Here is a deployment that will never be ready because it requires its pods
to be scheduled on a node with a label that doesn't exist in the cluster:

```shell
echo '
apiVersion: apps/v1
kind: Deployment
metadata:
  name: some-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: some-app
  template:
    metadata:
      labels:
        app: some-app
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: no-such-node
                    operator: In
                    values:
                      - "true"
      containers:
        - name: pause
          image: registry.k8s.io/pause:3.9
' | kubectl apply -f -
deployment.apps/some-app created
```

Let's confirm that all the pods were created, but none of them are running:

```shell
❯ kubectl get po
NAME                        READY   STATUS    RESTARTS   AGE
some-app-55cb6c5586-25gcj   0/1     Pending   0          117s
some-app-55cb6c5586-6xg2x   0/1     Pending   0          15s
some-app-55cb6c5586-b4sc7   0/1     Pending   0          15s
```

Alright, let's cause more havoc and create a deployment for Nginx with an invalid image name:

```shell
echo '
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
        - name: nginx
          image: nnnnnnnnginx #  👈 invalid image name
' | kubectl apply -f -

deployment.apps/nginx created
```

Let's check the status of our cluster now:

```shell
❯ kubectl get po
NAME                        READY   STATUS         RESTARTS   AGE
nginx-74f5dd8d8f-zfdmw      0/1     ErrImagePull   0          34s
some-app-55cb6c5586-25gcj   0/1     Pending        0          9m3s
some-app-55cb6c5586-6xg2x   0/1     Pending        0          7m21s
some-app-55cb6c5586-b4sc7   0/1     Pending        0          7m21s
```

So, we have two deployments, one of them has Three pending pods and the other one is in error state. Let's ask k8s-ai to
help us:

```
❯ python main.py 
☸️ Interactive Kubernetes Chat. Type 'exit' to quit.
----------------------------------------------------
👤 You: what's the cluster's status?
🤖 AI: The current status of the Kubernetes cluster is as follows:

### Nodes
- **Control Plane Node**: `k8s-ai-control-plane` is in a **Ready** state and running version **v1.33.1**.

### Pods Status
- **Running Pods**:
  - `coredns`: `coredns-674b8bbfcf-rrjdz` and `coredns-674b8bbfcf-w89zr` are both running successfully.
  - `etcd`: Running on `etcd-k8s-ai-control-plane`.
  - Network and Control components like `kindnet`, `kube-apiserver`, `kube-controller-manager`, `kube-proxy`, 
    and `kube-scheduler` are all running.
  - `local-path-provisioner`: Running.

- **Troubled Pods**:
  - In the `default` namespace:
    - `nginx-74f5dd8d8f-zfdmw` has an `ImagePullBackOff` issue.
    - Several `some-app` pods are in a `Pending` state.

### Services
- **ClusterIP Services**:
  - `kubernetes` service is running at IP `10.96.0.1`.
  - KubeDNS service is available at `10.96.0.10` with ports `53/UDP, 53/TCP, 9153/TCP`.

Overall, the cluster's core components and system pods are operational, but there are issues with 
applications in the `default` namespace that need addressing, particularly the `ImagePullBackOff` 
and `Pending` statuses.
```

OK. That's a pretty good summary. Let's ask it what's the problem with the pending pods:

```
👤 You: find out why the some-app pods are pending
🤖 AI: The `some-app` deployment is configured with a node affinity rule that cannot be satisfied 
by the current  cluster node configuration. The specific node affinity configuration is as follows:

affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: no-such-node
          operator: In
          values:
          - "true"

This configuration is attempting to schedule the pods on nodes that have a label `no-such-node` 
with the value `"true"`. However, the current node, `k8s-ai-control-plane`, does not possess such a 
label. This results in the pods being unable to be scheduled.

### Steps to Correct the Issue:

1. **Modify the Deployment's Node Affinity**:
   - If the affinity rules are not necessary, consider removing or adjusting them from the
     deployment.
   - If specific node selection criteria are required, ensure that the cluster nodes are 
     labeled accordingly.

2. **Label the Node** (if you intend to keep the affinity rule):
   - Add the required label to the node if the intent is to only run `some-app` pods on a 
     specific subset of nodes. 
   Given the current setup, this would involve adding a label like `no-such-node=true` to 
   `k8s-ai-control-plane`, should this be the intended setup.

Would you like to proceed with modifying the deployment configuration or adding a label to the current node?
----------
```

Nice. Let's ask k8s-ai to add the needed label so the pods can be scheduled:

```
👤 You: add the label no-such-node to our control plane node
🤖 AI: The label `no-such-node=true` has been successfully added to the control plane node 
   `k8s-ai-control-plane`.
----------
👤 You: what kubectl commands did you use?
🤖 AI: I used the following `kubectl` commands:
1. `kubectl get nodes` - This command was used to list all the nodes in the Kubernetes cluster to identify
    the control plane node.
2. `kubectl label nodes k8s-ai-control-plane no-such-node=true` - This command was used to add the label 
    `no-such-node=true` to the control plane node named `k8s-ai-control-plane`.
----------
```

As you can see k8s-ai can execute multiple operations to accomplish a task. In this simple case, it first listed the
nodes, then it added the label to the control plane node. Let's check the status of the pods now:

```shell
kubectl get po
NAME                        READY   STATUS             RESTARTS   AGE
nginx-74f5dd8d8f-zfdmw      0/1     ImagePullBackOff   0          35m
some-app-65696dbff4-2cph8   1/1     Running            0          2m27s
some-app-65696dbff4-8gbp8   1/1     Running            0          2m28s
some-app-65696dbff4-lxgfb   1/1     Running            0          3m13s
```

Excellent. The pods are running now. Let's see if k8s-ai can fix our nginx deployment:

```
👤 You: let's go back to the nginx deployment. suggest options how to fix it
🤖 AI: It looks like there is an issue with the `nginx` deployment due to the incorrect image name. 
   The image name `nnnnnnnnginx` seems to be invalid or misspelled for the standard `nginx` image. 
   Here are some options to fix the issue:

1. **Update the Image Name:**
   - Correct the image name in the deployment to a valid `nginx` image, such as `nginx:latest`.
2. **Roll Back the Deployment:**
   - If there was a previous version of the deployment with a valid configuration, you can roll back to
     that version if the deployment history is available.
3. **Check Image Repository:**
   - Verify whether the image exists in your container registry if you're using a custom image. Make 
     sure it's accessible without authentication issues.
4. **Check Compatibility:**
   - Ensure that the specified image version is compatible with your Kubernetes cluster version.
Would you like me to go ahead with the first option and update the image name in the deployment?
----------
```

Those all sound like good options. Let's go with the first one and update the image name to `nginx:latest`:

```
👤 You: option 1 sounds good. go for it.
🤖 AI: The nginx deployment has been updated with the correct image name and successfully rolled out. 
   If you have any more questions or need further assistance, feel free to ask!
----------
```

Alright. Now, that we trust k8s-ai we don't need to run `kubectl get pods` commands ourselves we can just ask k8s-ai to
do it for us.

```
👤 You: show me the pods
🤖 AI: The pods are up and running successfully:
- **nginx-5869d7778c-wjcsz**: Running
- **some-app-65696dbff4-2cph8**: Running
- **some-app-65696dbff4-8gbp8**: Running
- **some-app-65696dbff4-lxgfb**: Running
The nginx deployment is now fixed and operational. If you need further assistance, feel free to ask!
```

## 🫣 Looking behind the curtain 🫣

That was pretty impressive. right? How does this Kubernetes "agent" work? Check
out [k8s-ai](https://github.com/the-gigi/k8s-ai/tree/v1.0.0). It is a complete AI framework including a text
chat interface and a full-fledged Kubernetes AI "agent" that can diagnose and fix any problem in your cluster and let
you interact with your cluster in natural language. The whole thing is 60 lines of Python.

The actual agentic loop that does all the heavy lifting is just 18 lines. Let's break it down.

We begin by importing the necessary packages and configuring the OpenAI client to use the gpt-4o model. The API key must
be available in the OPENAI_API_KEY environment variable:

```python
import os
import sh
import json
from openai import OpenAI

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
model_name = "gpt-4o"
```

Next, we define the kubectl tool in the format required by OpenAI's function calling syntax. Pretty much we specify that
the LLM can call kubectl with any arguments.

```python
tools = [{
    "type": "function",
    "function": {
        "name": "kubectl",
        "description": "execute a kubectl command against the current k8s cluster",
        "parameters": {
            "type": "object",
            "properties": {
                "cmd": {
                    "type": "string",
                    "description": (
                        "the kubectl command to execute (without kubectl, just "
                        "the arguments). For example, 'get pods'"
                    ),
                },
            },
            "required": ["cmd"],
        },
    },
}]
```

Then, we have the actual agentic loop implemented in the little `send()` function. It accepts a list of messages (
including the latest user message) and sends them to the LLM (gpt-4o in this case) though the OpenAI API via the
client.chat.completions.create() method. Note that we pass the tools array we defined abive with the kubectl tool. The
API returns a response that may be final or it may contain tool calls. If it contains tool calls, we check that the
request tool is a kubectl command. If it is, we extract the command from the tool call and execute it using the
sh.kubectl() method. Then we append the result to the messages list and call `send()` again recursively with the updated
message list that includes the result of the `kubectl` command. If the response does not contain any tool calls, then it
is the final response from the model and we return its content.

```python
def send(messages: list[dict[str, any]]) -> str:
    response = client.chat.completions.create(
        model=model_name, messages=messages, tools=tools, tool_choice="auto")
    r = response.choices[0].message
    if r.tool_calls:
        message = dict(
            role=r.role,
            content=r.content,
            tool_calls=[dict(id=t.id, type=t.type, function=dict(name=t.function.name, arguments=t.function.arguments)
                             ) for t in r.tool_calls if t.function])
        messages.append(message)
        for t in r.tool_calls:
            if t.function.name == 'kubectl':
                cmd = json.loads(t.function.arguments)['cmd'].split()
                result = sh.kubectl(cmd)
                messages.append(dict(tool_call_id=t.id, role="tool", name=t.function.name, content=result))
        return send(messages)
    return r.content.strip()
```

Finally, here is the `main()` function that interacts with the user and invokes the agentic loop. It initializes the
messages list with a simple system prompt. and then runs in a loop where it accepts user input, appends it to the
message list and calls the send() function that may invoke the kubectl tool any number of times until it returns a final
answer, which will be printed to the console and then wait for the next user input.

Note the cool 😎 use of the [walrus operator](https://peps.python.org/pep-0572/) (:=) to assign the user input to a
variable
and check if it is not equal to 'exit' in a single line.

```python
def main():
    print("☸️ Interactive Kubernetes Chat. Type 'exit' to quit.\n" + "-" * 52)
    messages = [{'role': 'system', 'content': 'You are a Kubernetes expert ready to help'}]
    while (user_input := input("👤 You: ")).lower() != 'exit':
        messages.append(dict(role="user", content=user_input))
        response = send(messages)
        print(f"🤖 AI: {response}\n----------")


if __name__ == "__main__":
    main()
```

## 🤔 Where is the agent? 🤔

So, we went through each and every line of the code. All there is a little loop that calls the LLM repeatedly and if the
LLM requested to invoke kubectl with some arguments it does it. There is no autonomous behavior, no perception, no
reasoning and no action orientation. All the smart behavior of analyzing the cluster and fixing the problems is an
emergent behavior of the LLM itself. So, AI "agent" is really just a fancy name for a system prompt and a set of tools.

## 💎 Let's talk about fancy stuff 💎

But, but, but… what about all the fancy stuff that AI agents are supposed to do? 🤔 What about memory 🧠, RAG 📚, dynamic
model selection 🎛️, Self-referencing agents 🪞 and all that jazz? 🎷 Well, it turns out that you can do all that with the
same paradigm of agentic loop + tools 🛠️.

That said, sometimes it is more natural and efficient to build some meta-capabilities into the AI framework itself 🧱.
Let’s discuss some important use cases 🧐.

🧠 Memory 🧠

LLMs have no memory 😶. If you saw the movie [50 First Dates](https://www.youtube.com/watch?v=rKVZ1iNInO0), you know what
I mean. 🎥
In every call to the LLM we must provide it the entire context of the conversation 📝. If you run a program like k8s-ai
then as long as it’s running it will append messages to the context, but if you restart it all the in-memory memory (see
what I did there?) is gone 🗑️. It’s possible to implement long-term persistent memory, by saving the messages to a file
or a database 🗃️ and loading it when the program starts. Now, memory can be implemented in the AI framework itself, but
it can also be implemented as a set of tools (e.g. list_conversations, load_conversation, save_conversation, etc.) 🛠️.
When a user asks the LLM about their previous conversation it can use the tool to automatically load the conversation
and have access to all the history 🔄.

📚 RAG 📚

RAG (retrieval-augmented generation) is a technique that allows LLMs to access external knowledge sources 🌐. It can also
be implemented as a set of tools that the LLM can call to retrieve information from external sources 🧰. It is also
possible to implement RAG at the AI system level by pre-processing queries to the LLM and deciding, which external
information would be useful, but that kind of defeats the purpose of having a magical LLM that figure out better than
you what information is needed ✨. Note that, sometimes it is necessary to use these pre-processing RAG techniques for
very valid reasons ✅. My point is that there is nothing inherently special about RAG that can’t be done as a tool 🧩.

🎛️ Dynamic model selection 🎛️

Now, we get into crazyland territory 😵. The agentic loop is called with a specific model (gpt-4o for k8s-ai). What if
mid-processing the LLM realizes that it’s not up to the task and needs to delegate to a smarter model? 🧠 Or the
opposite — maybe the task is trivial and can be accomplished by a simpler and cheaper model 💵. Well, all it takes is to
define a tool like call_llm() that takes the model name and a list of messages 💬. The tool can be called from within the
agentic loop and it will invoke a new instance of k8s-ai with the specified model and will have all the context of the
conversation so far 🔁. It will run its own agentic loop and return the result to the original LLM that will return it to
the user 🔙.

🤝 Multi-agent systems 🤝

The same concept applies to so-called multi-agent systems 🕸️. You can have multiple “agents” running in parallel and
they can call each other as tools 🛠️. This is a very powerful technique that allows you to build complex hierarchical
systems with multiple “agents” that can collaborate and share information 🔗. The agents can be specialized (have special
system prompts) in different areas and they can call each other as needed 👥. But, still there is nothing there. The LLM
decides at each point which “agent” to invoke, by selecting a specific system prompt and a set of tools 🎯.

Note that when considering distributed multi-agent systems, it may be better to introduce something like the
Agent2Agent (A2A) protocol 🌍, but even that can be encapsulated in a tool where the tool utilizes internally the
networking needed to reach remote agents 📡.

🧑‍🔧 Self-modifying agents 🧑‍🔧

Alright. Let’s take it to the next level 🚀. Why should our AI system be limited by the configuration (system prompts and
set of tools) we provide it? What if the LLM decides that it needs to change its own system prompt or add new tools? 🧠
Well, you guessed it. You can define a tool that allows the LLM to modify its own configuration 🪛. This is a very
powerful technique that allows you to build self-modifying systems that can adapt to new situations and learn from their
experiences 📈. But, again, there is nothing special about it. It’s just a tool that allows the LLM to modify its own
configuration 🔧.

## 🏡 Take-home points 🏡

- AI agents don't exist. They are just a pattern for interacting with LLMs.
- What is referred to as an AI agent is just a system prompt and a bunch of tools.
- A vey simple AI framework can be used to simulate arbitrarily complex AI agents.
- Creative use of prompts tools can make the AI agent concept seem real.

🇳🇱 **Blijf vreemd, mijn vrienden**
