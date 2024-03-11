+++
title = 'EKS IP Address Assignment'
date = 2024-03-10T20:12:31-07:00
+++

It was a dark night. The wind was howling outside. Suddenly, I got a Slack message that our EKS
cluster has run out of IP addresses 😱. To be continued...

<!--more-->

Kubernetes is this thing that orchestrates containerized workloads that run on a bunch of nodes.
Yes, I'm  aware that [it does a few other things too](https://www.amazon.com/Kubernetes-operate-world-class-container-native-systems/dp/1804611395).

So, we have this hierarchy where each Kubernetes cluster has multiple nodes, each node has
multiple pods (in theory a node may be empty, but in practice there are always daemonsets) and each
pod has one or more containers.

```
Kubernetes Cluster
|
+-- Node 1
|   |
|   +-- Pod A
|       |
|       +-- Container A1
|
+-- Node 2
    |
    +-- Pod B
    |   |
    |   +-- Container B1
    |
    +-- Pod C
        |
        +-- Container C1
        +-- Container C2
```

Today, we don't care about the containers. Deal with it!

Kubernetes has a very simple networking model - each pod in the cluster has a unique IP address. The
question is where this IP address comes from. The answer is that it comes from the IPAM (IP address
management)plugin of the configured CNI plugin. In a nutshell Kubernetes itself has no idea about
any networking details. It just defines a specification called CNI (Container Networking Interface)
and each Kubernetes distribution comes with a CNI plugin that implements the specification and also
has a separate executable (IPAM plugin) it invokes. Check out the gory details here:
https://github.com/containernetworking/cni/blob/spec-v0.4.0/SPEC.md

Alright, who cares? Pods get their unique IP address somehow and everyone is happy. right?

Well, almost... different Kubernetes distributions use different CNI plugins with different
strategies, configuration options and subtle dependencies on your nodes and cloud provider.
When planning your cluster it is vital to understand the interplay between all these components
or else you'll run into errors like:

```
desc        = failed to setup network for sandbox "12345678" 
plugin-type = "aws-cni" 
name        = "aws-cni" 

failed (add): add cmd: failed to assign an IP address to container
```

Back to our story... when I received this message I started to investigate. Here is the situation,
The cluster in question is a multi-az EKS cluster with 3 subnets of /22. That means that in each
availability zone we have about 1024 IP addresses (give or take). The problem happened when the
number of nodes in the cluster was about 80 and there were about 800 pods scheduled. Those nodes
and pods were distributed pretty evenly across all the AZs, so there should have been plenty of IP
addresses to go around.

The logical conclusion was that EKS is pre-allocating IP addresses per node even if they aren't used
yet. I've run into a similar situation before with AKS. AKS used to look at the `maxPodsPerNode` of
a node spec and pre-allocates ALL the IP addresses to that node ensuring that whenever a pod is
scheduled to the node it will have an IP addresses ready for it. This behavior is great for
performance, but very wasteful when your nodes are configured with `maxPodsPerNode=250` even when on
average you have less than 30 pods per node. AKS doesn't do that anymore and has a dynamic IP
allocation that ensures there are always between 8 and 16 available IP addresses per node. But, the
behavior I observed on EKS was more complicated.

Let's break it down. EKS nodes are AWS instances (duh!). AWS instances can have one or more network
interfaces (ENIs). Each ENI can have a number of IP addresses associated with it. Now, here is the
thing - the number of ENIs and the max number of IP addresses per ENI depends on the instance type.
Beefier instance types get more ENIs and more IP addresses per ENI.

Here is a table with some partial data that demonstrate it:

```
---------------+----------------------------+-------------------------------------
Instance type  | Maximum network interfaces | Private IPv4 addresses per interface
---------------+----------------------------+-------------------------------------
m3.large       | 3                          | 10
m3.xlarge      | 4                          | 15
m3.2xlarge     | 4                          | 30
m4.large       | 2                          | 10
m4.xlarge      | 4                          | 15
m4.2xlarge     | 4                          | 15
m4.4xlarge     | 8                          | 30
m4.10xlarge    | 8                          | 30
m4.16xLarge    | 8                          | 30
m5.large       | 3                          | 10
m5.xlarge      | 4                          | 15
m5.2xlarge     | 4                          | 15
m5.4xlarge     | 8                          | 30
m5.8xlarge     | 8                          | 30
---------------+----------------------------+-------------------------------------
```

In our case, our nodes' instance type supported up to 8 ENIs and 30 IP addresses per ENI for
a maximum of 240 IP addresses. Note that this number tells you what's the maximum number of pods
Kubernetes will be able to schedule on the node (although a couple of IP addresses are used by the
node itself).

But, actually checking one the nodes showed 60 IP addresses associated with it. There were about 10
pods on the node. What's going on? Don't panic.

The AWS CNI plugin employs a method where each node begins with a pre-provisioned ENI, referred to
as a "warm" ENI. This warm ENI is automatically populated with the maximum number of IP addresses
that it can accommodate. For instance, if we consider a node that supports up to 30 IP addresses per
ENI, it would start with a warm ENI already provisioned with 30 IP addresses, ready for use.

```
Empty Node (No Pods):
+------------------+      +------------------+
|       Node       |      |   Warm ENI 1     |
|                  |----->| 30 IP Addresses  |
+------------------+      +------------------+
```

When a pod is deployed to the node, it is allocated an IP address from this warm ENI. This
allocation reduces the number of available IP addresses to 29. AWS CNI anticipates the need for more
addresses as more pods are scheduled, so it proactively attaches a new warm ENI, also with 30
pre-allocated IP addresses. Consequently, the node has 60 IP addresses at its disposal, even though
only one is currently in use by the pod.

```
Node with a pod  (First Pod Scheduled):
+------------------+      +------------------+     +------------------+
|       Node       |      |      ENI 1       |     |   Warm ENI 2     |
| 1 Pod (Uses 1 IP)|----->| 29 IP Addresses  |---->| 30 IP Addresses  |
+------------------+      +------------------+     +------------------+
```

As more pods are added, they continue to consume IP addresses from the first ENI until it is fully
utilized. Once all IP addresses from the first ENI are allocated, any additional pods will then
start to use IP addresses from the second ENI. At this stage, to maintain the "warm" state, a third
ENI with another set of 30 IP addresses is attached to the node, ensuring that there is always a
buffer of available IP addresses for new pods.

```
Node with many pods (40 Pods Scheduled, 30 IPs from ENI 1, 10 IPs from ENI 2):
+--------------------+      +-----------------+     +------------------+     +------------------+
|       Node         |      |     ENI 1       |     |      ENI 2       |     |  Warm ENI 3      |
|40 Pods (Use 40 IPs)|----> | 0 IP Addresses  |---->| 20 IP Addresses  |---->| 30 IP Addresses  |
+--------------------+      +-----------------+     +------------------+     +------------------+
```

To be super precise the node itself also uses two IP addresses, but I ignored it to simplify the
diagrams :-). If we want to go into full pedantic mode then pods that use `hostNetwork=true` reuse
the node's IP address and don't consume an additional IP address when scheduled.

OK. What's the moral of the story? You need to be aware of how many IP addresses are going to be
pre-allocated to your nodes to understand how many nodes your subnets can support (remember that the
IP addresses allocated to nodes and pods come from your cluster subnets). So Three /22
subnets combine for 3072 IP addresses. When nodes require 60 IP addresses each the cluster can
support just 51 nodes.

That's not a lot. What can be done? Lots of stuff! let's go through the list:

1. Use larger subnets - you can quadruple the number of nodes you support with /20 subnets (4096 IP
   addresses per subnet)
2. Use smaller nodes - nodes where the number of IP addresses per ENI is small will not waste so
   many IP addresses in the warm ENI
3. Configure the AWS CNI daemonset to pre-allocate less than the full capacity of the warm ENI
4. Switch to IPv6

There are a lot of interesting conversations about these options, their pros and cons and when it's
appropriate to use each one. But, this post is long enough as is.

Check out these links if you want to explore further the gnarly details of the AWS CNI plugin, its
IP address management subtleties and various IP address optimization strategies:
https://aws.github.io/aws-eks-best-practices/networking/vpc-cni/
https://aws.github.io/aws-eks-best-practices/networking/ip-optimization-strategies/

Until next time...