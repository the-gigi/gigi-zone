+++
title = 'Kubernetes Upgrades Are Officially Boring'
date = 2024-10-20T17:39:07-07:00
categories = ["Kubernetes", "DevOps"]
+++

In the olden days 🏰 (a few years ago) upgrading a Kubernetes cluster was a stressful task 😰 that
could bring the system down 💥 or at the very least cause major disruption, deployment moratorium 🚫,
and significant toil for most of the engineering team 😓. I'm happy to report that this is no longer
the case 🎉...

<!--more-->

![](yawn-upgrade.png)

## 🌅 Present day - California 🌅

Yesterday I upgraded multiple EKS clusters from version 1.28 to version 1.31. It was the most
uneventful upgrade ever 💤. It just worked! ⚡

I upgraded the control plane of each cluster from 1.28 → 1.29 → 1.30 → 1.31, and then upgraded all
node groups from 1.28 → 1.31 in one fell swoop 🚀.

I ran [Pluto](https://pluto.docs.fairwinds.com/) before I started to ensure we don’t use any
deprecated or removed resources and APIs. We didn't have any 🏆! This is not a stroke of luck 🍀.
Kubernetes has become more stable. There are always Alpha and Beta versions of new resources, but
the fundamental resources have been generally available for years. The innovation happens at the
edges or
remains backward-compatible.

Kubernauts 🧑‍🚀 don’t have to "live in interesting times" anymore.

## 📜 The Olden days (Circa 2020) 📜

Kubernetes 1.16 was released on September 18, 2019. This was a major release since Kubernetes
stopped serving several important API groups, such as:

- extensions/v1beta1
- apps/v1beta1
- apps/v1beta2

You may not be on a first-name basis 🤔 with API groups from 15 versions ago, so let me bring you up
to speed 🛵. All these critical resources were served from those API groups:

- Deployment
- StatefulSet
- ReplicaSet
- DaemonSet
- NetworkPolicy
- PodSecurityPolicy

If you upgraded from 1.15 to 1.16 and tried to apply an apps/v1beta1 Deployment Kubernetes will
return an error like so:

```
echo 'apiVersion: apps/v1beta1
kind: Deployment
metadata:
  name: example
  labels:
    app: example
spec:
  replicas: 3
  template:
    metadata:
      labels:
        app: example
    spec:
      containers:
        - name: example
          image: nginx
          ports:
            - containerPort: 80
  selector:
    matchLabels:
      app: example' | kubectl apply -f -
      
error: resource mapping not found for name: "example" namespace: "" from "STDIN": no matches for
kind "Deployment" in version "apps/v1beta1" ensure CRDs are installed first      
```

At the time, I worked for a company managing tens of clusters and hundreds of workloads. Engineers
constantly pushed changes 🛠️, fiddling with manifests.

Kubernetes clusters can only move forward. Once upgraded, there is no way to roll back
🔙, so getting it right the first time was critical. Tools similar to Pluto existed, but the stakes
were too high 🎯 and I didn't trust them completely. We ran on GKE with lots of CRDs and operators
generating resources dynamically.

So, I developed a tool called "Upgradanator" 🛡️ to reduce upgrade risks. The tool replicated a
live cluster and all its resources tested for incompatibilities.

## 🛠️ Enter the Upgradanator 🛠️

The Upgradanator provisioned a new 1.16 GKE cluster without node pools. It then generated YAML
manifests for every resource that required upgrading.

Gigi, you may ask, how did it generate the YAML? Using `kubectl get all`? Absolutely not! 🚫 That
command is limited and doesn't return all resources, especially not CRDs.

Instead, I used a neat kubectl plugin called [ketall](https://github.com/corneliusweig/ketall) 🪄 for
the job.

Once the Upgradanator collected all YAML manifests, it applied them in dry-run mode on the 1.16
cluster—without nodes 🖥️—saving costs. Dry-run mode provides a complete compatibility check from the
API server without provisioning any resources.

These days, we can take it further using [vCluster](https://github.com/loft-sh/vcluster) 🎩, creating
virtual clusters for testing instead of real ones.

Shout out to everyone involved in reliably and predictably releasing rock solid versions of
Kubernetes every 3 months 🙏.

# 📖 References 📖

- [Deprecated APIs Removed In Kubernetes 1.16](https://kubernetes.io/blog/2019/07/18/api-deprecations-in-1-16/)
- [Pluto](https://pluto.docs.fairwinds.com/)
- [vCluster](https://github.com/loft-sh/vcluster)
