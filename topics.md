# Blog post topics

## Pwning Kubernetes

## Fixing the OpenAI Function Calling API

https://github.com/openai/openai-openapi/issues/259

https://github.com/sashirestela/simple-openai/issues/132

## Automating away AWS SSO Login

https://github.com/the-gigi/auto-aws-sso-login

## OpenAI JavaClient library

https://github.com/the-gigi/llm-playground-java/

## Test DB Connectivity

### First attempt

This requires that PGPASSWORD is defined in your local environment. Not excellent.

```
kubectl debug $(kubectl get po -o name | grep some-pod | head -n 1)                 \
  -it --image postgres -n some-namespace -- bash -c "PGPASSWORD=$PGPASSWORD psql  \
  -h the.proxy-cacj4bsngo6v.us-east-1.rds.amazonaws.com -U some-user -c '\dt' "
```

The password will also be visible to anyone in the cluster that can get pods as it is passed in the
spec as command argument.

### Second attempt

This is a little better, we run everything in a sub-shell, disable history and fetch the postgres
password from
AWS secret manager dynamically. It will be difficult to get the postgres password on our local
machine (unless attacker gets the AWS credentials of course).

```
(
  # Disable history in the subshell
  HISTFILE=
  set +o history

  PGPASSWORD=$(aws secretsmanager get-secret-value --secret-id postgres-secret | jq -r .SecretString | jq -r .postgresPassword)
  kubectl debug $(kubectl get po -o name | grep some-pod | head -n 1)                 \
  -it --image postgres -n some-namespace -- bash -c "PGPASSWORD=$PGPASSWORD psql  \
  -h $PGHOST -U some-user -c '\dt' "
  
 # Re-enable history (optional)
  set -o history
)
```

However, the password will still be visible to anyone in the cluster that can get pods as it is
passed in the
spec as command argument.

### Final attempt

The most secure way is to keep the postgres password in the cluster as secret. The secret can be
mounted to a container and in particularly to our container. Then, the PGPASSWORD environment
variable is set only when the command is executed in the cluster.

```
kubectl run --rm --image=postgres -it pgctl \
  -n $NAMESPACE \
  --overrides='
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
              "value": "'$PGHOST'"
            },
            {
              "name": "PGPASSWORD_FILE",
              "value": "/etc/secrets/postgresPassword"
            }
          ],
          "command": ["/bin/bash"],
          "args": ["-c", "PGPASSWORD=$(cat $PGPASSWORD_FILE) exec psql -U somr-user -d some-database"],
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
            "secretName": "some-secret"
          }
        }
      ]
    }
  }'
```

## Prompt Engineering (the old kind)

https://github.com/the-gigi/dotfiles/blob/master/components/prompt.sh

https://github.com/the-gigi/dotfiles/blob/master/rcfiles/.p10k.zsh


function db_connect() {
    NAMESPACE=$1
    PG_HOST=$2
    KUBE_CONTEXT=$3
    kubectl run --rm --image=postgres -it pgctl \
      -n $NAMESPACE --context $KUBE_CONTEXT \
      --overrides='
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
                  "value": "'$PG_HOST'"
                },
                {
                  "name": "PGPASSWORD_FILE",
                  "value": "/etc/secrets/postgresPassword"
                }
              ],
              "command": ["/bin/bash"],
              "args": ["-c", "PGPASSWORD=$(cat $PGPASSWORD_FILE) exec psql -U invisible -d invisible"],
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
                "secretName": "invisible"
              }
            }
          ]
        }
      }'
    }
}
