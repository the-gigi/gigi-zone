+++
title = 'Postgres on K8s'
date = 2024-05-30T16:52:57-07:00
+++

Your postgres DB 🌐 runs in the cloud with a private IP address. It requires a password 🔐. You need
to access it from your laptop for a quick psql session. What's the best way to do it 🤷 ? Keep
reading to find out...

<!--more-->

## Typical Scenario 📝

Let's start with a typical scenario:

- Your system is running on Kubernetes.
- You have workloads running on the cluster that access Postgres
- You have permissions to run pods on the cluster

We shall demonstrate that with a kind cluster

```
❯ kind create cluster -n postgres-on-k8s
Creating cluster "postgres-on-k8s" ...
 ✓ Ensuring node image (kindest/node:v1.27.3) 🖼
 ✓ Preparing nodes 📦
 ✓ Writing configuration 📜
 ✓ Starting control-plane 🕹️
 ✓ Installing CNI 🔌
 ✓ Installing StorageClass 💾
Set kubectl context to "kind-postgres-on-k8s"
You can now use your cluster with:

kubectl cluster-info --context kind-postgres-on-k8s

Have a nice day! 👋
```

Before we start, I use this alias `k='kubectl'`. If you don't you're simply bananas 🍌

Let's store the Postgres password in a secret:

```shell
❯ k create secret generic postgres-secret --from-literal=POSTGRES_PASSWORD=the-password
secret/postgres-secret created
```

Next let's deploy Postgres on our cluster. That involves creating a persistent volume, a persistent
volume claim, a deployment and finally a service. Yes, I know that's some wall of YAML 🧱.

```yaml
> echo '
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pg-pv
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: "/mnt/data"
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pg-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:latest
          env:
            - name: POSTGRES_DB
              value: mydatabase
            - name: POSTGRES_USER
              value: myuser
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: POSTGRES_PASSWORD
          ports:
            - containerPort: 5432
          volumeMounts:
            - mountPath: /var/lib/postgresql/data
              name: pgdata
      volumes:
        - name: pgdata
          persistentVolumeClaim:
            claimName: pg-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  ports:
    - port: 5432
  selector:
    app: postgres
  ' | k apply -f -  
```

If you're unfamiliar with any of the above, just get the
📗 [Mastering Kubernetes](https://www.amazon.com/Kubernetes-operate-world-class-container-native-systems/dp/1804611395)
📗 book, read it cover to cover and get back here 😉.

Let's also have a pod that's accessing our database.

```yaml
echo '
apiVersion: v1
kind: Pod
metadata:
  name: query-pod
spec:
  containers:
    - name: query-container
      image: postgres:latest
      command: [ "/bin/sh", "-c" ]
      args:
        - |
          while true; do
            PGPASSWORD=$POSTGRES_PASSWORD psql -h postgres.default.svc.cluster.local \
             -U the-user -d the-database \
             -c "SELECT now();"
            sleep 30;
          done
      env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: POSTGRES_PASSWORD
  restartPolicy: OnFailure
  ' | k apply -f -  
```

## Check the Logs 📜

Great. Time to check the logs of our query pod to make sure everything is awesome 😛:

```shell
❯ k logs query-pod
              now
-------------------------------
 2024-05-31 01:07:14.974345+00
(1 row)

              now
-------------------------------
 2024-05-31 01:07:45.025832+00
(1 row)
```

## Connect to Postgres via psql 🛠️

Cool. Now, what do you need to connect to Postgres via psql?

- psql installed (duh!)
- The hostname, port, user and password
- Being able to reach the host IP address

Our query pod has the whole 3️⃣ Trifecta 3️⃣. But, we're outside the cluster :-(

## Options to Connect 🌐

In general, there are two options:

1. You can bring Kubernetes to you
2. You can go to the Kubernetes

Translation...

1. port-forward the Postgres service and access it locally
2. Run a pod or exec into an existing pod in the cluster

## Port-Forward Method 🌉

Let's start with the port-forward method:

```shell
❯ kubectl port-forward svc/postgres 5432:5432
Forwarding from 127.0.0.1:5432 -> 5432
Forwarding from [::1]:5432 -> 5432
```

Now, the mountain has come to us and we can connect to postgres via localhost:

```shell
❯ PGPASSWORD=the-password psql -h localhost -U the-user -d the-database
Handling connection for 5432
psql (14.11 (Homebrew), server 16.3 (Debian 16.3-1.pgdg120+1))
WARNING: psql major version 14, server major version 16.
         Some psql features might not work.
Type "help" for help.

the-database=# select now();
              now
-------------------------------
 2024-05-31 01:26:15.357622+00
(1 row)
```

That's pretty dope. But, port-forward is not everyone's cup of tea 🍵 (and for good reasons...).

Let's move on to the other method and just exec into our query-pod, get a shell and launch psql:

```shell
❯ k exec -it query-pod -- bash 
root@query-pod:/# PGPASSWORD=the-password psql -h postgres.default.svc.cluster.local \
             -U the-user -d the-database
psql (16.3 (Debian 16.3-1.pgdg120+1))
Type "help" for help.

the-database=# select now();
              now
-------------------------------
 2024-05-31 01:31:08.401884+00
(1 row)
```

If you're really in a hurry you can exec directly into psql

```shell
❯ k exec -it query-pod -- bash -c \
   'PGPASSWORD=the-password psql -h postgres.default.svc.cluster.local -U the-user -d the-database'
psql (16.3 (Debian 16.3-1.pgdg120+1))
Type "help" for help.

the-database=# select now();
              now
-------------------------------
 2024-05-31 01:40:00.408435+00
(1 row)
```

### Problems with `kubectl exec` 🚫

There are several problems with doing `k exec` into an existing pod. First, maybe there is no pod
running with psql installed. Second, even if there is you need to find it. Third, the pod you
connected to might disappear any time. It is much better form to just run your own pod instead of
piggybacking over an existing pod.

## Creating a Pod 💻

If we just create a pod like so:

```yaml
❯ echo '
apiVersion: v1
kind: Pod
metadata:
  name: pgctl
spec:
  containers:
    - name: pgctl
      image: postgres
      stdin: true
      tty: true
      command: [ "/bin/bash" ]
      args:
        - "-c"
        - "PGPASSWORD=the-password exec psql -h postgres.default.svc.cluster.local -U invisible -d invisible"
  restartPolicy: Never
  ' | k apply -f -
```

Then, we still need to exec to it.

### Using `kubectl run` with Overrides ⚙️

Instead, we need to use `k run` with some fancy overrides:

```yaml
❯ kubectl run --rm --image=postgres -it pgctl --overrides='
  {
"apiVersion": "v1",
"spec": {
  "containers": [
    {
      "name": "pgctl",
      "image": "postgres",
      "stdin": true,
      "tty": true,
      "env": [
        {
          "name": "PGHOST",
          "value": "postgres.default.svc.cluster.local"
        },
        {
          "name": "PGPASSWORD",
          "value": "the-password"
        }
      ],
      "command": [ "/bin/bash" ],
      "args": [
        "-c",
        "exec psql -U the-user -d the-database"
      ]
    }
  ]
}
}'

  the-database=# select now();
  now
  -------------------------------
  2024-05-31 02:52:37.186006+00
  (1 row)
```

Amazing. That gets us pretty far, but there are two problems. First, we need to know the password (
AKA `the-password`) in order to run this command. Second, once our pod is running the postgres
password will be visible to anyone who has the permissions to get pods in the cluster.

```shell
❯ k get po pgctl -o yaml | yq '.spec.containers[0].env[1]'
name: PGPASSWORD
value: the-password
```

This is a major security concern because all kinds on unsavory characters and tools might have
permissions to get pods in your cluster.

How about we take advantage of secret postgresPassword. We can mount this secret into our container
and extract the password at runtime.

```yaml
❯ kubectl run --rm --image=postgres -it pgctl --overrides='
  {
    "apiVersion": "v1",
    "spec": {
      "containers": [
        {
          "name": "pgctl",
          "image": "postgres",
          "stdin": true,
          "tty": true,
          "env": [
            {
              "name": "PGHOST",
              "value": "postgres.default.svc.cluster.local"
            },
            {
              "name": "PGPASSWORD_FILE",
              "value": "/etc/secrets/POSTGRES_PASSWORD"
            }
          ],
          "command": [ "/bin/bash" ],
          "args": [
            "-c",
            "PGPASSWORD=$(cat $PGPASSWORD_FILE) exec psql -h $PGHOST -U the-user -d the-database"
          ],
          "volumeMounts": [
            {
              "name": "secret-volume",
              "mountPath": "/etc/secrets"
            }
          ]
        }
      ],
      "volumes": [
        {
          "name": "secret-volume",
          "secret": {
            "secretName": "postgres-secret"
          }
        }
      ]
    }
  }'

  the-database=# select now();
  now
  -------------------------------
  2024-05-31 03:09:03.556052+00
  (1 row)
```

What does it do exactly? This command creates a temporary pod to interactively connect to a
Postgres database using psql, then automatically deletes the pod once the session ends.
It uses a Kubernetes secret to securely provide the Postgres password to the pod,
avoiding hard-coding sensitive information in the pod specification.

## Putting it all together 🧩

We got a solid solution now, but it's not that user-friendly. Every time we want to connect to
Postgres we need to fetch that long command from somewhere. The host name, the username, the
database name, the secret name are all hard-coded. Let's make a shell function out of it and support
optional environment variables too:

```yaml
function connect_db() {
  local PGHOST=${1:-$PGHOST}
  local PGUSER=${2:-$PGUSER}
  local PGDATABASE=${3:-$PGDATABASE}
  local PGSECRET=${4:-$PGSECRET}
  local PGPOD=${5:-pgctl}


  if [ -z "$PGSECRET" ]; then
echo "Error: PGSECRET is not set."
  return 1
  fi

  kubectl run --rm --image=postgres -it $PGPOD --overrides='
  {
    "apiVersion": "v1",
    "spec": {
      "containers": [
        {
          "name": "pgctl",
          "image": "postgres",
          "stdin": true,
          "tty": true,
          "env": [
            {
              "name": "PGHOST",
              "value": "'"$PGHOST"'"
            },
            {
              "name": "PGPASSWORD_FILE",
              "value": "/etc/secrets/POSTGRES_PASSWORD"
            }
          ],
          "command": [ "/bin/bash" ],
          "args": [
            "-c",
            "PGPASSWORD=$(cat $PGPASSWORD_FILE) exec psql -h $PGHOST -U '"$PGUSER"' -d '"$PGDATABASE"'"
          ],
          "volumeMounts": [
            {
              "name": "secret-volume",
              "mountPath": "/etc/secrets"
            }
          ]
        }
      ],
      "volumes": [
        {
          "name": "secret-volume",
          "secret": {
            "secretName": "'"$PGSECRET"'"
          }
        }
      ]
    }
  }'
}
```

Add this function to your profile and you can connect easily using

```shell
❯ connect_db postgres.default.svc.cluster.local the-user the-database postgres-secret

the-database=# select now();
              now
-------------------------------
 2024-05-31 06:58:48.586882+00
(1 row)
```

If you want two sessions use a different pod name than `pgctl` (the default):

```shell
❯ connect_db postgres.default.svc.cluster.local the-user the-database postgres-secret pgctl2

the-database=# select now();
              now
-------------------------------
 2024-05-31 07:03:12.829764+00
(1 row)
```

## Final Words 💎

One last thing before you go. Everything we covered here works for managed Postgres as well (AWS
RDS, Google Cloud SQL, Azure Database for Postgres).

Give it a try and have fun!


