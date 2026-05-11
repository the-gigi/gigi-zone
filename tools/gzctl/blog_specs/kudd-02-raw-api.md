KUDD #02. Slug: kubectl-deep-dive-02-raw-api.

Title: Kubectl Deep Dive - Talking to the Raw API

Series: Kubectl Deep Dive (KUDD). Second installment, follows #01 (Be KinD).

Audience: Same as KUDD #01. Daily Kubernetes users who already know `kubectl get pods` and want to understand what is actually happening under the hood. The whole premise of this post is the reveal that kubectl is a thin HTTP client and you can do everything it does without it.

Bottom line: The Kubernetes API is a regular REST server reachable over HTTPS. kubectl is just one client (and arguably not always the best one). This post shows three ways to talk to the API server directly: `kubectl proxy` (cheap and cheerful), `kubectl get --raw` (uses kubectl's auth without spawning a proxy), and `curl` (full control, bring your own TLS and token). Then it shows the parts of the API that kubectl does not surface nicely: discovery, OpenAPI schema, watches, /healthz, /metrics, and a couple of fun corners.

Personal angle: Every time I am stuck debugging a weird kubectl issue, the answer is to drop down to raw HTTP. Watching the wire is the fastest way to learn what a controller is actually doing. Once you see kubectl as one of many HTTP clients, a lot of mysticism around Kubernetes evaporates.

Series index: This is KUDD #02. Link back to #01 (Be KinD) in the intro using the Medium series list convention. For KUDD the series list lives on Medium under a list with both posts; for #02 it is short enough to just link inline to the previous post(s).

Date: 2026-05-10

Categories: Kubernetes, Kubectl, KUDD, API, DevOps

Closing greeting: Greek. Flag emoji 🇬🇷. "Αντίο, φίλοι!" (Antio, fili!) — "Goodbye, friends!" — chosen because "Kubernetes" itself comes from the Greek κυβερνήτης (kybernetes, helmsman/governor). Fits a post about going back to the API roots.

Lab: All commands run on a local kind cluster from KUDD #01. The cluster used while drafting is named `raw-api` (single node) so it shows up in command output as `raw-api-control-plane`.

Section outline:

1. Hook + bolded quote + <!--more--> + hero.png
   - 3-5 sentences. Sprinkle 3-4 emoji naturally. The hook: "kubectl is just an HTTP client". The cluster is a REST API server. Once you see that, a lot of Kubernetes stops looking like magic. This post drops down a layer and shows how to call the API directly, three different ways, with a real kind cluster.
   - Quote candidates:
     - "Everything is a file." ~ Unix philosophy (echoing "Everything is a REST endpoint")
     - "Any sufficiently advanced technology is indistinguishable from magic." ~ Arthur C. Clarke (chosen — kubectl looks like magic until you peel it back)
   - Use the Clarke quote.
   - Mention this builds on KUDD #01 (Be KinD) and link to it.

2. ## 🔧 kubectl is Just an HTTP Client 🔧
   - The big reveal. Every kubectl command is one or more HTTPS requests to the API server.
   - Prove it with `kubectl get pods -v=8 -n kube-system 2>&1 | grep -E 'GET|POST|curl-command'` (show the actual curl-equivalent kubectl prints at -v=8). Truncate output to the interesting lines (the constructed URL and the request method). Lead with one or two of the request/response lines.
   - One paragraph on the structure of the URLs: `/api/v1/...` for core resources, `/apis/<group>/<version>/...` for grouped resources, `/api/v1/namespaces/<ns>/pods` for namespaced things.
   - Diagram (diagram-api-stack.png): kubectl on the left, an HTTPS lock icon in the middle, kube-apiserver on the right with /api, /apis, /openapi, /healthz, /metrics endpoints listed inside.

3. ## 🛰️ Three Ways to Reach the API 🛰️
   - Brief overview before drilling into each.
   - Diagram (diagram-three-paths.png): Three lanes. Lane 1 "kubectl proxy" — local loopback HTTP, kubectl handles auth. Lane 2 "kubectl get --raw" — kubectl talks HTTPS directly, no proxy. Lane 3 "curl" — you handle TLS and auth tokens yourself.
   - The tradeoffs: proxy is the easiest for ad-hoc exploration. `--raw` is best for scripting. curl is for when kubectl gets in the way (or when there is no kubectl, like inside a pod).

4. ## 🪞 kubectl proxy 🪞
   - What it does: starts a local HTTP server (default port 8001) that forwards to the API server using your kubeconfig credentials. From your shell, you talk plain HTTP to localhost, kubectl proxy talks HTTPS to the cluster.
   - The minimal example:
     ```
     $ kubectl proxy &
     Starting to serve on 127.0.0.1:8001
     $ curl -s http://127.0.0.1:8001/api/v1/namespaces/kube-system/pods | jq '.items | length'
     11
     ```
   - Show a real `curl http://127.0.0.1:8001/api` response (the version list) and `/api/v1` (the list of resources). These are useful for understanding what the API server actually exposes.
   - Mention the security note: by default proxy binds to 127.0.0.1, which is fine for local exploration. Don't bind it to a real interface unless you know what you are doing — anyone who can reach the port gets full cluster admin rights as whoever started the proxy.
   - Note when proxy is exactly what you want: hitting the Kubernetes dashboard, services accessed via the proxy path (`/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy/`).
   - Show how to kill it cleanly when done (`kill %1`).

5. ## 🪶 kubectl get --raw 🪶
   - This is the lightweight version. No proxy, no curl. kubectl makes the HTTPS request for you using your current context, but returns whatever the API server responds with verbatim (no formatting, no -o json/yaml dance).
   - Examples to include:
     ```
     kubectl get --raw /api
     kubectl get --raw /api/v1 | jq '.resources[].name'
     kubectl get --raw /apis | jq '.groups[].name'
     kubectl get --raw /healthz
     kubectl get --raw '/api/v1/namespaces/kube-system/pods?limit=2' | jq '.items[].metadata.name'
     ```
   - Best use case: scripts that need to hit an endpoint kubectl does not have a verb for, or that want raw JSON without coaxing kubectl's printers.
   - Pair with `kubectl version --output=json` to remind people kubectl has structured output for the things it does cover; --raw is for the things it does not.

6. ## 🐚 curl Directly 🐚
   - The "I want to do this from a script, possibly without kubectl" path. Two things to handle yourself: TLS verification and authentication.
   - Walk through pulling the API server URL and credentials from kubeconfig:
     ```
     APISERVER=$(kubectl config view --raw -o jsonpath='{.clusters[0].cluster.server}')
     ```
   - For kind clusters, the credential is a client cert + key embedded in kubeconfig. Show how to extract them:
     ```
     kubectl config view --raw -o jsonpath='{.users[0].user.client-certificate-data}' | base64 -d > /tmp/client.crt
     kubectl config view --raw -o jsonpath='{.users[0].user.client-key-data}' | base64 -d > /tmp/client.key
     kubectl config view --raw -o jsonpath='{.clusters[0].cluster.certificate-authority-data}' | base64 -d > /tmp/ca.crt
     curl --cacert /tmp/ca.crt --cert /tmp/client.crt --key /tmp/client.key $APISERVER/api/v1/namespaces/kube-system/pods | jq '.items | length'
     ```
   - Important note: kind uses cert auth. Many real clusters use bearer tokens (a ServiceAccount token or an OIDC token). Show the token flavor briefly:
     ```
     TOKEN=$(kubectl create token default)
     curl --cacert /tmp/ca.crt -H "Authorization: Bearer $TOKEN" $APISERVER/api/v1/namespaces/default/pods
     ```
   - Mention that inside a pod the canonical pattern is:
     - TOKEN at /var/run/secrets/kubernetes.io/serviceaccount/token
     - CA at /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
     - APISERVER at https://kubernetes.default.svc
   - Cleanup: remove the temp files. Sensitive material.

7. ## 🔍 What the API Actually Exposes 🔍
   - Now that we have three ways in, show the interesting endpoints kubectl does not give you a verb for. Use `kubectl get --raw` for these (cleanest).
   - **Discovery**:
     - `kubectl get --raw /api` → versions list (just `v1` for core).
     - `kubectl get --raw /apis` → all API groups and versions. This is what `kubectl api-resources` consumes under the hood.
   - **OpenAPI schema**:
     - `kubectl get --raw /openapi/v3` → an index of OpenAPI documents per group/version.
     - `kubectl get --raw /openapi/v3/api/v1 | jq '.components.schemas | keys[]' | head` → the actual schemas. This is what powers `kubectl explain`.
   - **Health and readiness**:
     - `kubectl get --raw /healthz` → returns `ok` if the API server is healthy.
     - `kubectl get --raw '/livez?verbose'` and `/readyz?verbose` show per-check status. Handy when debugging a sick control plane.
   - **Version**:
     - `kubectl get --raw /version` returns the server's version info. Same data `kubectl version` formats.
   - **Metrics**:
     - `kubectl get --raw /metrics | head` → Prometheus exposition format. Same data Prometheus scrapes off the API server. Show 5-6 lines of the output (request counts, etcd stuff).

8. ## 📡 Watching Without kubectl 📡
   - The Kubernetes watch protocol is HTTP long-poll: a GET with `?watch=true&resourceVersion=N` keeps the connection open and streams newline-delimited JSON events as objects change.
   - Demonstrate with `kubectl get --raw`:
     ```
     kubectl get --raw '/api/v1/namespaces/default/pods?watch=true' &
     kubectl run hello --image=busybox -- sleep 3600
     ```
   - Show the stream of events (ADDED for the pod, then a MODIFIED for the status update).
   - Explain why this matters: every controller in Kubernetes (kube-controller-manager, kubelet, custom operators) is basically a long-running watch loop on a small set of resources. Once you have seen the raw stream, controllers stop being mysterious.

9. ## 🧭 When To Reach For This 🧭
   - Be honest. Most of the time kubectl is the right tool. The raw API is the right tool when:
     - You are debugging a kubectl bug, a permissions issue, or a strange caching problem. Drop to curl and you remove kubectl as a variable.
     - You are writing a controller or operator and want to understand what your code will actually see on the wire.
     - You need an endpoint kubectl does not have a verb for: /metrics, /openapi/v3, /healthz subpaths, custom verbs.
     - You are inside a pod with no kubectl binary but you do have the ServiceAccount mount.
     - You are talking to a managed service that exposes the Kubernetes API but adds funky auth (e.g., AKS AAD pod-managed identity, EKS aws-iam-authenticator) and you want to confirm the auth path is working.

10. ## ⏭️ What's Next ⏭️
   - Future KUDD posts to tease (pick 4-5):
     - Server-side apply vs client-side apply, field managers, conflicts
     - How does `kubectl port-forward` actually work? (SPDY/websockets)
     - Watches, `kubectl wait`, and why `--wait` beats `sleep`
     - JSONPath, custom-columns, go-template output sorcery
     - `kubectl explain` and the OpenAPI schema we touched today
     - kubectl plugins and the krew ecosystem

11. ## 🏠 Take Home Points 🏠
   - kubectl is an HTTP client. Everything it does is a REST call to the API server. -v=8 shows you the wire.
   - `kubectl proxy` gives you cheap localhost HTTP access for ad-hoc exploration and the dashboard.
   - `kubectl get --raw` is the cleanest way to script against endpoints kubectl does not have a verb for.
   - `curl` directly when you want to remove kubectl from the equation, or you are inside a pod with no kubectl binary.
   - The interesting endpoints kubectl does not surface: /openapi/v3 (what powers explain), /healthz and /livez (control plane health), /metrics (Prometheus scrape), /version (server version), watches (the heart of every controller).

12. Book plug — KUDD uses the **Mastering Kubernetes** plug (paperback ASIN 1804611395). Not the AI book.

13. Greek closing: 🇬🇷 Αντίο, φίλοι! 🇬🇷

Tone notes:
- Conversational, first-person, confident. Same voice as KUDD #01.
- Avoid AI-style: no em dashes, minimize bullet lists in the prose, no "bespoke"/"leverage"/"delve". Use commas, periods, parentheses, colons. Keep Take Home Points and the topic-list bullets only.
- No markdown tables.
- Use real captured command output. The cluster in use is named `raw-api`, so expect `raw-api-control-plane` in output. Do not fabricate output.

Spelling convention: kubectl is lowercase everywhere (it is the binary name). KinD is capital-K capital-D in prose when referring to the project. API server, kube-apiserver, kubeconfig, kubelet stay lowercase per Kubernetes convention. ServiceAccount and ResourceVersion stay PascalCase when they refer to the Kubernetes type.

Images:
- hero.png: Cartoon in xkcd-friendly style. A curtain being pulled back to reveal a friendly REST API behind it. The curtain has a "kubectl" label, behind it is a desk with a sign "kube-apiserver — REST inside". A small figure looks surprised and delighted. Soft warm colors, white background.
- diagram-api-stack.png: A horizontal diagram. Left: a small kubectl box (with the kubectl logo or just the word). Middle: an arrow labeled HTTPS with a padlock. Right: a larger box labeled "kube-apiserver" containing five small sub-boxes for the endpoints /api, /apis, /openapi/v3, /healthz, /metrics. Clean, white background, light blue boxes.
- diagram-three-paths.png: Three parallel horizontal lanes from a "you" stick figure on the left to the kube-apiserver on the right. Lane 1 labeled "kubectl proxy" passes through a "localhost:8001 (HTTP)" box. Lane 2 labeled "kubectl get --raw" goes straight through a "kubectl + kubeconfig" box. Lane 3 labeled "curl" passes through a "TLS + token (you handle it)" box. Same clean light style as diagram-api-stack.png.

Notes for drafting:
- Run every command on the `raw-api` kind cluster and paste real output. Trim long outputs but mark trims with `...` so readers know.
- The first time `-v=8` is shown, only include 3-5 of the most informative lines (request method, URL, request headers excluded for brevity).
- When showing `/metrics`, only show 5-6 representative lines (one HELP/TYPE pair, two metric samples).
- Word count target: 1800-2400. Same density as KUDD #01.
- Remember to clean up: `kind delete cluster --name raw-api` is the only command not in the article but worth running yourself.
