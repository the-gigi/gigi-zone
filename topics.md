# Blog post topics

## OpenAI JavaClient library

https://github.com/the-gigi/llm-playground-java/

## Test DB Connectivity

kubectl debug $(kubectl get po -o name | rg some-pod | head -n 1)                 \
  -it --image postgres -n some-namespace -- bash -c "PGPASSWORD=$PGPASSWORD psql  \
  -h the.proxy-cacj4bsngo6v.us-east-1.rds.amazonaws.com -U some-user -c '\dt' "

ChatGPT breakdown:
https://chat.openai.com/share/e/7d36fc4d-0e0e-480e-90aa-1bc284377099


## Automating away AWS SSO Login

https://github.com/the-gigi/auto-aws-sso-login


## Prompt Engineering (the old kind)

https://github.com/the-gigi/dotfiles/blob/master/components/prompt.sh

https://github.com/the-gigi/dotfiles/blob/master/rcfiles/.p10k.zsh

