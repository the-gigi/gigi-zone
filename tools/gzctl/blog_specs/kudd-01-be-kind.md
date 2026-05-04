KUDD #01. Slug: kubectl-deep-dive-01-be-kind.

Title: Kubectl Deep Dive - Be KinD

Series: Kubectl Deep Dive (KUDD). This is the inaugural post.

Audience: Readers who already use Kubernetes and kubectl day to day. The series will not rehash the kubectl man page. It will focus on interesting, less-common, or commonly misunderstood corners of kubectl and the Kubernetes API surface.

Bottom line: All of the Kubectl Deep Dive series will run on local kind clusters, so installment #1 sets up the lab. Show how to install kind, create a single-node cluster, create a multi-node cluster (control plane + workers) with a config file, and a few quality-of-life tips that make kind a joy to live with day to day.

Personal angle: Gigi has used minikube and k3d in the past for local Kubernetes. These days he's all in on kind. Open with that journey briefly so the reader knows the choice is opinionated, not religious. minikube was the first one he used. k3d is great if you want lightweight k3s, but for testing real-cluster behavior (multi-node, Docker images, ingress, networking) kind has been the most predictable.

Why kind for this series:
- It runs each Kubernetes node as a Docker container. That makes multi-node trivial without a VM.
- It uses upstream kubeadm-built nodes, so the cluster behaves like a real cluster (closer to prod than k3s/k3d for many things, especially when the article topic is API-level behavior).
- Fast to create and tear down. The series will create and destroy clusters constantly.
- The kubectl context is wired up automatically, so there is zero setup friction after `kind create cluster`.

Series index: This is post #01, so no Medium series list exists yet. Establish the series here. Future posts will link back to a Medium series list (to be created). For #01, just say "this is the inaugural post in a new series, Kubectl Deep Dive" and tease the upcoming topics.

Date: 2026-05-03

Categories: Kubernetes, Kubectl, KUDD, Kind, DevOps, LocalDev

Closing greeting: German. Flag emoji 🇩🇪. "Auf Wiedersehen, Freunde!" — chosen because "Kind" in German means "child", which echoes the post title.

Section outline:

1. Hook + bolded quote + <!--more--> + hero.png
   - The hook: 4-6 sentences introducing the new series. Mention that it assumes the reader knows kubectl basics. Sprinkle 3-4 emoji naturally. Optional: a fun aside (e.g., kubectl pronunciation joke). Tease that future posts will dig into raw API access, server-side apply, port-forward internals, watches, vcluster, kubectl plugins, JSONPath sorcery, and more.
   - Quote: something pithy on local development or simplicity. Possible options:
     - "Premature optimization is the root of all evil." ~ Donald Knuth (use only if it fits cleanly)
     - "Make it work, make it right, make it fast." ~ Kent Beck
     - "Simple things should be simple. Complex things should be possible." ~ Alan Kay (favorite — fits kind's philosophy)
   - Use the Alan Kay quote.

2. ## 🐳 Why Local Kubernetes 🐳
   - Why you want a local cluster at all: experimentation, blast radius zero, fast iteration, no cloud bill, plane rides.
   - The local-k8s landscape: minikube, k3d, kind, Docker Desktop, Rancher Desktop, Orbstack, Colima.
   - Gigi's personal arc: minikube first (great onboarding, VM-heavy). k3d for the lightweight k3s love. These days all in on kind because it's a real upstream cluster in Docker containers, fast multi-node, and the closest thing to "prod-shaped" without paying for prod.
   - Brief: when you might still pick something else (single-binary k3s for edge, minikube for the addon ecosystem).

3. ## 🚀 Installing Kind 🚀
   - Brew on macOS: `brew install kind`
   - Linux: download the binary from GitHub releases (link to https://kind.sigs.k8s.io/docs/user/quick-start/)
   - Verify: `kind version`
   - Prerequisite: a working Docker daemon (Docker Desktop, OrbStack, Colima, Rancher Desktop — any will do).
   - Quick sanity check: `docker ps` should work.

4. ## 🌱 Your First Cluster 🌱
   - The one-liner: `kind create cluster`
   - What that does under the hood (briefly): pulls a node image, runs a single Docker container as the control plane, runs kubeadm inside it, writes the kubeconfig context to `~/.kube/config` and switches to it.
   - Show the output (paste actual output from a run).
   - Verify: `kubectl cluster-info`, `kubectl get nodes`. Single node named `kind-control-plane`.
   - Naming: `kind create cluster --name dev` — show that you can name your clusters and have several side by side.
   - Listing: `kind get clusters`
   - Deleting: `kind delete cluster --name dev`
   - The kubectl context: `kubectl config get-contexts` — kind names them `kind-<clustername>`.

5. ## 🏘️ Multi-Node Clusters 🏘️
   - Why you'd want multi-node locally: testing taints, tolerations, affinity, daemonsets, real scheduling behavior, pod-to-pod networking across nodes, draining and disruption budgets.
   - The config file approach. Show a complete YAML config:
     ```yaml
     # kind-multi.yaml
     kind: Cluster
     apiVersion: kind.x-k8s.io/v1alpha4
     name: multi
     nodes:
       - role: control-plane
       - role: worker
       - role: worker
       - role: worker
     ```
   - Create with: `kind create cluster --config kind-multi.yaml`
   - Show the result: `kubectl get nodes -o wide` (4 nodes, one labeled control-plane, three workers).
   - Quick note on HA: kind also supports multiple control-plane nodes for HA testing, but that's overkill for most series posts. Mention it as a footnote. Example with three control-plane and three workers, shown briefly.
   - The killer feature: each node is just a Docker container. `docker ps` to see them all. `docker exec -it multi-worker bash` to poke at one (kind names node containers `<clustername>-<role>`, not `kind-<clustername>-<role>`).

6. ## 🛠️ Kind Quality of Life 🛠️
   - A short, opinionated grab-bag of things that make kind feel native:
     - **Loading local images**: `kind load docker-image my-app:dev --name multi`. No registry needed during dev. Explain why this matters: kind nodes are isolated Docker containers, so they can't see images on your host's Docker daemon by default.
     - **Port mappings**: in the kind config, `extraPortMappings` exposes node ports to localhost. Show a snippet for ingress on 80/443.
     - **Cluster scoped to a directory**: each kind config can pin a name. Combine with `direnv` to switch contexts automatically when you cd into a project. (Foreshadow direnv post on topics.md if appropriate.)
     - **Fast teardown**: `kind delete clusters --all` nukes everything. Useful between blog post drafts.
     - **Mounting host paths**: `extraMounts` for binding host directories into nodes. Useful when testing CSI or anything that needs real disk on the node.

7. ## ⏭️ What's Next ⏭️
   - Tease the next several KUDD posts (reuse the topic list, lightly grouped). Suggested teasers:
     - Talking to the raw Kubernetes API (kubectl proxy, kubectl get --raw, curl)
     - Server-side apply vs client-side apply, and the field manager story
     - How does kubectl port-forward actually work?
     - Watches, kubectl wait, and why --wait beats sleep
     - Multi-cluster magic with vcluster
     - kubectl plugins and the krew ecosystem
     - JSONPath, custom-columns, and other output sorcery
     - kubectl debug: ephemeral containers and node debug
     - kubectl auth can-i and --as impersonation
     - Discovery: api-resources, api-versions, shortnames, categories
     - dry-run modes (client vs server) and kubectl diff
     - The three flavors of kubectl patch
     - kubeconfig mechanics and KUBECONFIG merging
   - Keep the list to 4-6 bullets max (don't overpromise). Pick the most enticing.

8. ## 🏠 Take Home Points 🏠
   - kind is the most production-shaped local Kubernetes for the price (free) and the speed (seconds).
   - Single-node cluster: `kind create cluster`. Done.
   - Multi-node cluster: a tiny YAML config with `role: worker` entries.
   - Each kind "node" is a Docker container. That makes it trivially fast and easy to introspect.
   - Use `kind load docker-image` to ship local images into the cluster without a registry.
   - All future posts in the Kubectl Deep Dive series will run on kind. If you can follow along on your laptop, you'll get the most out of the series.

9. Book plug — KUDD series uses the **Mastering Kubernetes** plug (paperback ASIN 1804611395), not the default AI book. See the KUDD override in CLAUDE.md → "Book Plug" section.

10. German closing greeting: 🇩🇪 Auf Wiedersehen, Freunde! 🇩🇪

Tone notes:
- Conversational, first-person, confident.
- Light humor sprinkled in. No emoji in body prose, only in section headers and the hook.
- Avoid AI-style: no em dashes, minimize bullet lists in the prose itself, no "bespoke"/"leverage"/"delve". Use commas, periods, parentheses, colons. Keep Take Home Points as bullets per series convention.
- No markdown tables. Convert any "tool comparison" thoughts to flowing prose or short lists.
- Personal voice: when introducing the local-k8s history, say things like "I started with minikube years ago, dabbled with k3d, and these days I'm all in on KinD."

Spelling convention: in prose, headings, and the title, the project is styled **KinD** (capital K, capital D). In commands, YAML fields, identifiers (`kind-control-plane`, `kind-kind`), filenames, image names (`kindest/node`), CNI name (`kindnet`), URLs, and pasted output, leave it lowercase as-is — those are literal.

Images:
- hero.png: A friendly cartoon container ship docked next to a small island shaped like the kubectl steering wheel logo. On the deck of the ship, a few cargo containers labeled "control-plane" and "worker", with smiling faces. Title placard near the ship reads "Be KinD". xkcd-ish, warm tone.
- diagram-kind-arch.png: Simple diagram. Box labeled "Your Mac". Inside it, a "Docker daemon" box. Inside Docker, three boxes labeled as kind node containers (one control-plane, two workers). Arrows showing kubectl from outside Docker talking to the API server inside the control-plane node. Caption: "kind = Kubernetes nodes as Docker containers".
- diagram-kind-flow.png (optional, low priority): Flowchart of `kind create cluster` steps: pull node image -> start container -> run kubeadm init -> write kubeconfig context. Skip if it adds noise.

Notes for drafting:
- Cite kind official site (https://kind.sigs.k8s.io) once.
- Use real command output paste-ins where it helps. Run actual kind commands when drafting and paste the output, don't fabricate.
- Cluster name examples: use `dev` and `multi` consistently.
- Don't oversell kind. Be honest that it's not perfect (no built-in load balancer for Service type LoadBalancer; needs MetalLB or kind's cloud-provider-kind for that). Brief mention is fine, full coverage is a future post.
