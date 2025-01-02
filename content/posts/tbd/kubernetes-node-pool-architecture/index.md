Here are some common patterns:

### One big shared node pool

This is the simplest and default pattern. You have a single node pool with a single instance type.
All the nodes are identical. This is great for simplicity and ease of management. But, it's not
great for bin packing. It's unlikely that all your workloads with their different shapes will fit
neatly into one type of node. Your workloads will also share nodes with system workloads.

[](images/single-shared-node-pool.png)

### Shared Pool + Multiple Dedicated Node Pools

This another common pattern. Often you have workloads with special requirements like GPU or fast
local storage that are not needed by other workloads. Creating dedicated node pools for these
workloads ensure that they can get exactly the resources they need and don't have to compete with
other workloads. This is great for bin packing too as you can plan exactly how many pods you want to
pack into each node and customize the node available resources to the resource requests of the
workload.

The downside is that you have to manage multiple node pools can carefully configure labels and
selectors.


### System Pool + Shared Pool + Multiple Dedicated Node Pools

### Multiple node pools with the same shape in different sizes

### Multiple identical node pools different availability zones

NOT multi-az node pool

### Multiple node pools with the same shape in different sizes

### Failover node pools with same labels but different instance types
