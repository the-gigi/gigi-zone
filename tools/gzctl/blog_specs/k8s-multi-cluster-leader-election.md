Slug: k8s-multi-cluster-leader-election

Title: Kubernetes Leader Election Across Clusters (with a GitHub Gist as the Lock)

Standalone Kubernetes post (not part of CCDD or PEP Talk). The article walks through leader election in Kubernetes, starting from the basics inside one cluster, then breaking out to the genuinely interesting part: doing it across clusters with a GitHub Gist as the shared lock. Anchored on the working project at https://github.com/the-gigi/k8s-multi-cluster-leader-election.

Hook: open with the classic high-availability problem. You want N replicas for redundancy, but only one of them should actually do the work at any given moment (a controller, a cron-like job runner, a singleton consumer). That is leader election. In a single cluster Kubernetes makes it almost free. Across clusters, you need to get creative.

Pull quote candidate: "There can be only one." (Highlander). Or a riff on consensus being easy until the network shows up.

Important framing: the GitHub Gist trick in the demo is a teaching aid, not a production recipe. The real-world guidance comes later in the article and is the opposite: if you are already running a cross-cluster distributed system, you almost certainly have a global state store you depend on for other things. Use that. Do not introduce new infrastructure (and a new failure mode) just for leader election.

Key content points:

1. Why leader election exists. Active/passive HA, controllers, sharded-but-singleton workloads, anything that must not double-run. Contrast with stateless replicas where every pod can serve traffic.

2. The Kubernetes-native happy path. Walk through `client-go`'s `leaderelection` package: the `LeaderElector`, `LeaderElectionConfig`, `LeaseLock`, lease/renew/retry durations, and the `OnStartedLeading` / `OnStoppedLeading` / `OnNewLeader` callbacks. Show a minimal Go snippet so readers see the shape of the API. Mention that this is what kube-controller-manager and kube-scheduler use under the hood.

3. The lock interface is the pivot point. `resourcelock.Interface` is small: Get, Create, Update, RecordEvent, Identity, Describe. The built-in implementations (`LeaseLock`, `ConfigMapLock`, `EndpointsLock`) all live in etcd, which is per-cluster. The interface is the seam that lets us go elsewhere.

4. Why cross-cluster is hard. etcd is not designed to span regions. You could federate, you could stand up a global Postgres or DynamoDB or Consul, but that is a lot of infrastructure for "pick one pod across two clusters." We want something dumber.

5. The Gist trick (as a teaching device). A GitHub Gist is just a tiny key/value blob behind an authenticated HTTP API with optimistic concurrency (via the Gist revision) and zero infra to run. Implement `resourcelock.Interface` against the GitHub API. Store the same `LeaderElectionRecord` JSON the built-in locks store: `holderIdentity`, `leaseDurationSeconds`, `acquireTime`, `renewTime`, `leaderTransitions`. The `leaderelection` package does not care where the bytes live. State plainly: this is to prove the seam works, not because anyone should run production HA against gist.github.com.

6. Walk through the demo setup. The project uses `vcluster` to spin up three virtual clusters (napoleon, stalin, cleopatra) inside a single kind cluster. Each one runs the same leader-elector pod. They all point at the same Gist. Show what the Gist contents look like during steady state, then kill the leader and watch a candidate from a different cluster take over.

7. Why you should NOT use GitHub Gist in production:
   - GitHub API rate limits. A renew loop will eat your quota.
   - GitHub uptime becomes part of your HA story. If api.github.com is down, no one renews; the lease expires; election thrashes. You just made GitHub a dependency for your own availability.
   - Latency variance. HTTP round-trips to a third party are not predictable enough for tight lease durations.
   - The gist scope on a personal access token is broad. Service-account hygiene gets awkward.
   - It is funny. Funny is not a non-functional requirement.

8. What to actually use: pick the global store you already have. The core principle: if you are already running a cross-cluster distributed system, you have a global state store somewhere (databases, object storage, service discovery, secrets). It is already on your runbook, your oncall, your monitoring, your security review. Adding leader election to it costs you nothing operationally. Standing up a new system just for leader election doubles your failure surface for negative benefit. Walk through the realistic options:

   Cloud-managed (strongly consistent, multi-region):
   - Google Cloud Spanner. Yes, excellent fit. External consistency across regions, transactional CAS, but pricey and only worth it if you are already on it.
   - Azure Cosmos DB. Yes, with the right consistency level. Use Strong or Bounded Staleness for locks, not Session or Eventual. The default Session level will bite you.
   - AWS DynamoDB. Single-region with conditional writes is great for locks (this is what many production systems use). Global Tables across regions is last-writer-wins eventually consistent, which is wrong for locks. Pin the lock to one region even in a multi-region deployment.
   - Object storage with conditional writes: S3 (now supports conditional writes), GCS (generation-match preconditions), Azure Blob (ETag preconditions). Cheapest option if you only need a handful of locks.

   Open source (self-hosted or managed):
   - etcd. The obvious choice if you can run it across clusters; it is what the in-cluster lock already uses. Cross-region etcd is operationally heavy because of Raft latency, but doable.
   - Consul. HashiCorp's KV with WAN federation between datacenters and a built-in session/lock primitive. Designed for exactly this.
   - ZooKeeper. Battle-tested ephemeral nodes for locks; observers can extend reach across DCs. Unfashionable but it works.
   - CockroachDB, YugabyteDB, TiDB. Multi-region, strongly consistent SQL databases. If you are already running one, a `SELECT ... FOR UPDATE` on a leader row is fine.
   - PostgreSQL with advisory locks, if you have a single primary that is reachable from all clusters. Simple and underrated when one region is your control plane.
   - FoundationDB. Strict serializability, open source, multi-region capable. Niche but excellent.

   What to avoid:
   - Redis with RedLock for cross-region locks. The algorithm is contested (see Kleppmann's critique) and Redis replication is async by default. Single-instance Redis with `SET NX PX` is okay for non-critical locks; cross-region Redis for critical locks is not.
   - DNS, S3 without conditional writes, anything eventually consistent. If your store cannot do compare-and-swap, it cannot do locks.

9. Close with a recap: the small `resourcelock.Interface` is the seam, the lease record is just JSON, and the right backend is the one you are already running. Implementing a lock against your store of choice is left as an exercise for the reader.

Format notes:
- Standalone post, not part of a series. No series index, no "What's Next" section.
- Follow the standard structure: hook + quote + `<!--more-->` + hero image, emoji-bookend H2 sections, Take Home Points, book plug, closing greeting in a flag-wrapped foreign language not yet used in 2026 (Greek, Finnish, Italian, Polish, Hebrew are all open).
- Lots of diagrams. This topic begs for them.
- No markdown tables (Medium kills them). Use prose for comparisons.
- Link to the GitHub project early and again at the end.

Categories: Kubernetes, LeaderElection, HighAvailability, MultiCluster, Go

Date: TBD (next available slot)

Images:
- hero.png: vibrant hero image, three crowns floating above three Kubernetes clusters with a single glowing GitHub Octocat in the middle holding the "real" crown
- diagram-single-cluster.png: xkcd-style diagram of three pods in one cluster racing for a Lease object in etcd, one wins, others wait
- diagram-lock-interface.png: xkcd-style diagram showing `resourcelock.Interface` as a socket with `LeaseLock`, `ConfigMapLock`, and `GistLock` plugging into it
- diagram-cross-cluster.png: xkcd-style diagram with three vclusters (labeled napoleon, stalin, cleopatra) all pointing at one Gist in the cloud, arrows showing renew/acquire HTTP calls
- diagram-failover.png: xkcd-style sequence showing the leader pod dying, the Gist's `holderIdentity` changing, and a pod in a different cluster picking up the crown
