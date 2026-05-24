KUDD #03. Slug: kubectl-deep-dive-03-admission-granted.

Title: Kubectl Deep Dive - Admission Granted

Series: Kubectl Deep Dive (KUDD). Third installment. Follows #01 (Be KinD) and #02 (Talking to the Raw API).

Audience: Same as the previous KUDD posts. Daily Kubernetes users who already know what a pod and a webhook are. The hook is that as of 1.36, there is a new, native, much lighter way to do declarative mutation that lives inside the API server itself.

Bottom line: Kubernetes 1.36 promotes MutatingAdmissionPolicy to GA. It is a declarative, CEL-driven alternative to writing your own mutating admission webhook (or pulling in a full policy engine like Kyverno) for simple cases like injecting tolerations, labels, defaults, sidecars. Walk through a real-shaped use case: forcing e2e test pods onto dedicated tainted nodes when the API that creates the pods does not let the caller set tolerations. Show what it would take with a custom webhook, what it would take with Kyverno, and then show MutatingAdmissionPolicy doing it in 20 lines of YAML on a local kind cluster.

Personal angle: Recently I had to solve this exact problem at work. An e2e test suite ran on an EKS cluster with multiple node groups. We wanted the test pods on a dedicated test node group with a `dedicated=test:NoSchedule` taint so they could not be displaced by, or displace, regular traffic. The pods were created through an upstream API we did not own, and it did not surface tolerations. We solved it with a custom admission webhook plus a small Go server. It worked. But it was a whole new workload: a deployment, TLS cert rotation, RBAC, monitoring, availability concerns, the works. If we had been on 1.36 with MutatingAdmissionPolicy, the whole thing would have been a Kubernetes object.

Series index: This is KUDD #03. Link back to #01 and #02 in the intro using the same convention as #02. The Medium series list is short enough to still inline both links.

Date: 2026-05-24

Categories: Kubernetes, Kubectl, KUDD, Admission, DevOps

Closing greeting: Latin. Flag emoji 🇻🇦 (Vatican City — Latin is the official language). "Vale, amici!" — "Farewell, friends!" Chosen because "admission" comes from Latin *ad mittere* ("to send to") and the post is about gatekeeping at the API door. Roman doormen meet Roman language.

Lab: All commands run on a local kind cluster. Because there is no pre-built `kindest/node:v1.36.0` image as of this writing, I had to build one from the release artifacts with `kind build node-image --type release v1.36.0 --image kindest/node:v1.36.0`. The post should mention that explicitly so readers don't get stuck — they hit the same wall on a fresh `kind create cluster --image kindest/node:v1.36.0`. The cluster name is `admission` and the nodes are `admission-control-plane`, `admission-worker`, `admission-worker2`, `admission-worker3`. `admission-worker3` is the dedicated test node.

Section outline:

1. Hook + bolded quote + <!--more--> + hero.png
   - 3-5 sentences. The hook: admission control is the gate every resource has to pass through to get into the cluster. Until 1.36 the declarative options for *mutating* admission were limited (write your own webhook, or pull in Kyverno). 1.36 changes that with MutatingAdmissionPolicy going GA. Sprinkle 3-4 emoji naturally.
   - Quote: "The cheapest, fastest, and most reliable components of a computer system are those that aren't there." ~ Gordon Bell. Fits the theme — MutatingAdmissionPolicy eliminates the webhook server, the certs, the deployment.

2. ## 🚧 The Problem 🚧
   - Tell the real story. EKS, multiple node groups, e2e test pods needing to land on a dedicated `dedicated=test:NoSchedule` node group, upstream API that does not let the caller set tolerations. The webhook plus server we built. The reality that running a webhook is running a whole new workload.
   - Translate to a kind lab: a 4-node cluster, `admission-worker3` tainted `dedicated=test:NoSchedule` and labeled `dedicated=test`. A "test pod" the user wants to land there but no way to add tolerations from the create-time API.
   - Show: create the pod, it stays Pending or lands on the wrong node. We need a mutator.

3. ## 🚪 What is Admission Control 🚪
   - Brief refresher framed for someone who has heard the terms but is fuzzy on the order of operations. The API server request pipeline: authn → authz → mutating admission → schema validation → validating admission → etcd persistence.
   - Built-in admission controllers (NamespaceLifecycle, ServiceAccount, ResourceQuota, etc.) and the two external hooks: MutatingWebhookConfiguration and ValidatingWebhookConfiguration.
   - Diagram (diagram-admission-pipeline.png): horizontal pipeline through kube-apiserver showing each stage, with mutating admission box exploded into three lanes — built-in controllers, MutatingWebhookConfiguration, MutatingAdmissionPolicy (highlighted, "new in 1.36").

4. ## 🏗️ Option A: Roll Your Own Webhook 🏗️
   - The old shape: HTTPS server, TLS cert (signed by a CA the API server trusts), a Deployment, a Service, a MutatingWebhookConfiguration registering the URL and the resources you care about. You write the logic in Go (or whatever), parse an AdmissionReview, return a JSONPatch.
   - The hidden cost: another workload to babysit. Cert rotation. Availability (`failurePolicy: Fail` means a flaky webhook breaks pod creation, `Ignore` means mutations silently skip). RBAC for the webhook to do its job. Monitoring. Versioning the webhook image alongside your CRDs.
   - Show the *registration* YAML (5-10 lines) and a tiny pseudocode Go handler stub (maybe 10 lines, not real working code — just enough to make the point). Don't actually deploy it.
   - Honest line: "this is what I built at work. It was the right call at the time. In 2026 with 1.36 in reach, I'd reach for MutatingAdmissionPolicy first."

5. ## 🧰 Option B: Pull in Kyverno 🧰
   - Kyverno is a popular, mature, full-featured policy engine. It can mutate, validate, generate, verify images, generate policy reports, etc. The community is huge.
   - Show a 15-20 line Kyverno `ClusterPolicy` that does the toleration injection. Be honest: this is short and readable.
   - But: Kyverno is a full controller deployment, with its own CRDs (Policy, ClusterPolicy, PolicyException, PolicyReport, etc.), webhook server, leader election, multiple pods, RBAC, upgrades, helm chart. If your *only* mutation need is "inject these tolerations on e2e test pods", you're shipping a freight container for one envelope.
   - When Kyverno is the right call: when you have many policies, want validation+mutation+generation+image-verification all in one place, want policy reports and audit trails, multi-tenant policy delegation. Mention but don't dwell.

6. ## ✨ Option C: MutatingAdmissionPolicy (1.36 GA) ✨
   - The pitch: it's already in the API server. No webhook server, no controller deployment, no certs, no Deployment, no Service. You define two YAML objects and the API server handles the rest.
   - The two objects:
     - `MutatingAdmissionPolicy` — the *rule*. What to match, what to mutate, expressed in CEL.
     - `MutatingAdmissionPolicyBinding` — the *scope*. Which namespaces/objects this policy applies to. Letting the same policy be reused with different bindings is the parametrization story.
   - Walk through the YAML for the test-pod-tolerations case. Use ApplyConfiguration (server-side apply merge) for the toleration list because it merges cleanly with whatever else might be there. Use JSONPatch if SSA fights us — decide during cluster work, paste real output.
   - The CEL bit deserves a quick paragraph: CEL is the same expression language used by validating admission policies, the kubelet admission, and authorization webhooks. It is deliberately not Turing-complete and not allowed to make external calls. That last constraint is the entire point — the API server can evaluate it in-process, fast and predictable, without anyone running anything.
   - Apply it. Show the new pod creation. Show the pod now has the toleration. Show it landing on `admission-worker3`.

7. ## 🔬 Watching it Happen 🔬
   - Two ways to confirm the mutation:
     - The visible one: `kubectl get pod ... -o yaml` shows tolerations and nodeSelector that were not in the user's manifest.
     - The audit-trail one: enable a tiny audit policy and observe the request body before vs after. Optional; only if it fits without bloating the post. Otherwise just do the -o yaml diff.
   - Quick word on feature gates and API versions. In 1.34 and 1.35 the same policy is available as `admissionregistration.k8s.io/v1beta1`. In 1.36 it's GA at `v1`. The body of the spec is the same, only the apiVersion changed.

8. ## ⚖️ Picking Between the Three ⚖️
   - When to reach for each. Concrete bullets, not a table (Medium tables look bad — see CLAUDE.md):
     - **MutatingAdmissionPolicy**: simple, declarative mutations expressible as CEL over the incoming object. Injecting tolerations, default labels, default resource limits, basic sidecars. The default starting point in 1.36+.
     - **Kyverno (or Gatekeeper, or OPA)**: when you have many policies, want validation+mutation+generation under one roof, need policy reports, need image verification or background scanning, need policy exceptions as first-class resources.
     - **Custom webhook**: when you need to consult external state (a database lookup, a SaaS call, an ML model, a remote config service). MutatingAdmissionPolicy is CEL-only — no I/O, no external calls. Anything that needs to look outside the incoming request needs a webhook.

9. ## ⏭️ What's Next ⏭️
   - 4-5 future KUDD topics:
     - Server-side apply vs client-side apply, field managers, conflicts
     - kubectl port-forward internals (SPDY/websockets)
     - kubectl wait, watches, and why `--wait` beats `sleep`
     - JSONPath, custom-columns, output sorcery
     - ValidatingAdmissionPolicy (the validating sibling, GA'd earlier) and how mutating + validating compose

10. ## 🏠 Take Home Points 🏠
    - Admission control runs between authz and persistence. Mutating admission can change the object on the way in. Validating admission can reject it.
    - Until 1.36, declarative mutation meant a custom webhook (real workload, real maintenance) or a full policy engine like Kyverno (overkill for simple cases).
    - 1.36 GA's MutatingAdmissionPolicy and MutatingAdmissionPolicyBinding. Define a CEL expression, scope it with a binding, done. The API server handles it in-process.
    - CEL means no external calls. That is a feature, not a limitation — predictable evaluation, no extra workload, no availability story to manage.
    - When you need external state, keep the webhook. When you need a full policy program, keep Kyverno. For everything in between, MutatingAdmissionPolicy is the new default.

11. Book plug — KUDD uses the **Mastering Kubernetes** plug (paperback ASIN 1804611395). Not the AI book.

12. Latin closing: 🇻🇦 Vale, amici! 🇻🇦

Tone notes:
- Conversational, first-person, confident. Same voice as KUDD #01 and #02.
- Avoid AI-style: no em dashes, minimize bullet lists in the prose, no "bespoke"/"leverage"/"delve". Use commas, periods, parentheses, colons. Keep Take Home Points and topic-list bullets only.
- No markdown tables.
- Use real captured command output. The cluster is named `admission`, so expect `admission-control-plane`, `admission-worker`, `admission-worker2`, `admission-worker3` in output. Do not fabricate output.

Spelling convention: kubectl, kubeadm, kube-apiserver lowercase. KinD capital-K capital-D in prose. CEL is uppercase. ServiceAccount, MutatingAdmissionPolicy, MutatingAdmissionPolicyBinding, MutatingWebhookConfiguration stay PascalCase when referring to the Kubernetes type.

Images:
- hero.png: A friendly cartoon bouncer / Roman doorman at a velvet rope outside a club labeled "API server". The bouncer is holding a clipboard with "CEL" written on it, and stamping a sticker "tolerations: dedicated=test" on a small pod-shaped customer about to enter. Behind the rope, a queue of small pods. xkcd-friendly style, warm colors, white background. Latin/Roman touch on the bouncer's outfit.
- diagram-admission-pipeline.png: Horizontal pipeline through kube-apiserver. Stages left to right: Auth (authentication), AuthZ (authorization), Mutating Admission, Schema Validation, Validating Admission, etcd. The Mutating Admission box is expanded to show three lanes inside: "Built-in controllers", "MutatingWebhookConfiguration", "MutatingAdmissionPolicy (new in 1.36, highlighted)". Clean light blue boxes, white background.
- diagram-three-approaches.png: Three rows side by side, same visual scale, to show how much "stuff" each approach costs. Row 1 "Custom Webhook": cartoon of a server box + TLS cert + Service + MutatingWebhookConfiguration + a person on call. Row 2 "Kyverno": a larger box labeled "Kyverno controller" containing CRDs, multiple pods, leader election, webhook. Row 3 "MutatingAdmissionPolicy": two small YAML scrolls, an arrow, and the API server. Visual hint that row 3 is dramatically lighter than the other two.

Notes for drafting:
- Capture real output on the `admission` kind cluster. Trim long outputs but mark trims with `...`.
- Walk readers through the kind 1.36 image build step explicitly, including the `kind build node-image --type release v1.36.0 --image kindest/node:v1.36.0` invocation. Show that there is no pre-built image yet.
- Word count target: 1800-2400. Match KUDD #02's density.
- Cluster cleanup at the very end of the lab: `kind delete cluster --name admission`. Not in the article body, just a footnote.
