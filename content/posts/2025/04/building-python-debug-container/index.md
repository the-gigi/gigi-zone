+++
title = 'Building a Kubernetes Debug Container Image with Docker'
date = 2025-04-13T21:07:12-08:00
+++

Building optimized container images is a science 🧪 and an art 🎨. You need to know what you're doing to get it right. In
this post, we will build a Python-based 🐍 container image for troubleshooting Kubernetes ☸️️. Along the way, we will
discuss some of the best practices for building images, when they apply and when they don't! 🔍

For the impatient:  
https://github.com/the-gigi/docker-images/tree/main/py-kube

**“When you realize the difference between the container and the content, you will have knowledge.” ~ Idries Shah**

<!--more-->

![](images/hero.png)

Kubernetes is an unruly beast 🐉. I often need to get an inside look by running a debug container inside some pod or just
a standalone debug pod. I also like to have nice things when I debug, so I created my own container image with some
useful tools 🧰. Let's break it down file by file!

This is not an introduction to Docker 🐳, containers, or images! If you're new, let me GPT that for you:  
https://letmegpt.com/search?q=docker

## 📁 The .dockerignore 📁

When you build container images, you might end up with a bunch of files that we don't need in the final artifact. The
`.dockerignore` file tells Docker to ignore certain files and directories when building the image. This is similar to
`.gitignore` but for Docker.

```dockerignore
# Git files
.git
.gitignore

# Documentation
README.md

# Build scripts
build.sh

# Temporary files
*.tmp
*.swp
*~

# Logs
*.log
```

When using multi-stage builds where you explicitly copy files from one stage to another, the `.dockerignore` file is not
that important, because you can simply avoid copying unwanted files. So, the `.dockerignore` file is used as a
blacklist, where multi-stage builds are more like a whitelist.

## 🧱 The Dockerfile 🧱

The Dockerfile is the blueprint for your image. It contains all the instructions for building the image. There is a LOT
to talk about here. We will break it down into sections.

### 🧊 Picking a base image 🧊

First and foremost is the base image. You select it with the FROM statement.

```dockerfile
# syntax=docker/dockerfile:1.3

FROM python:3.13-slim@sha256:21e39cf1815802d4c6f89a0d3a166cc67ce58f95b6d1639e68a394c99310d2e5
```

Picking a base image is a crucial step in building a container image. You want to pick a base image that is small,
secure, and doesn't contain a lot of stuff you don't need. In this case, we are using the `python:3.13-slim` image,
which is a minimal version of the official Python image. It contains only the essential packages needed to run Python
applications. Note that I pinned the base image with a specific sha256 digest. This ensures that if I need to rebuild
the image, the exact base image will be used. This is best practice for predictability and security 🛡️ since newer
versions of the base image might have new vulnerabilities.

The reason I picked `python:3.13-slim` is that it is smaller than the full-fledged `python:3-13` image, but it still
contains a shell and everything needed to run Python scripts — which I want to do when I troubleshoot stuff 🐛. It is
based on the Debian 12 image (Bookworm).

### ⚙️ Build arguments ⚙️

Next, we define two build arguments: KUBECTL_VERSION, which the caller can set at build time to specify the desired
version of kubectl, and TARGETARCH, a built-in Docker variable that represents the target architecture. These are
especially important for creating multi-platform images that behave consistently across different environments.

```dockerfile
ARG KUBECTL_VERSION
ARG TARGETARCH
```

The reason we pass the `kubectl` version as a build argument is that we want to be able to build the image with
different versions of `kubectl`. As we will see later, unlike other tools, `kubectl` is not available from the official
APT repository.

### 🛠️ Installing OS-level dependencies 🛠️

The main job of the Dockerfile is to install dependencies on top of the base image. We use the `RUN` command to install
them. Now, each `RUN` command creates a new layer in the image. This means that if you change a single line in the
Dockerfile, all the layers after that line will be rebuilt. This can be time-consuming ⏳, so we want to minimize the
number of layers we create. The smallest possible number of layers is one. Let's do that!

The key is to chain all the commands we need with `&& \`

Here we install all the OS-level dependencies using `apt-get` (the Debian package manager):

```dockerfile
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
      vim \
      curl \
      tree \
      dnsutils \
      apt-transport-https \
      ca-certificates \
      netcat-openbsd \
      redis \
      gpg \
      bsdextrautils && \
      ...
```

We use `--no-install-recommends` to avoid installing unnecessary packages. This is a good practice to control precisely
what we install. We don't specify the version of the packages, which is a bit risky. But in this case, we sacrifice
some security for convenience. Managing explicit versions for every package is a lot of work. We will talk later about
scanning the final image to give us some peace of mind 🔍.

The `...` is there because we're about to install more stuff into the same layer.

### 📦 Installing kubectl 📦

So, it turns out there is no Debian package for `kubectl` in the official APT repository ¯\\_(ツ)_/¯. There are several
good reasons for that which I won't get into here. So, we need to do some extra legwork to install it. This block
installs `kubectl` from the official Kubernetes APT repository:

- Creates a secure directory for APT keyrings.
- Downloads and de-armors the GPG signing key.
- Adds the Kubernetes APT source URL for the given `KUBECTL_VERSION`.
- Updates APT metadata and installs the `kubectl` package.

It's a continuation of the same `RUN` command.

```dockerfile
    ...
    # Install kubectl
    mkdir -p -m 755 /etc/apt/keyrings && \
    curl -fsSL "https://pkgs.k8s.io/core:/stable:/v${KUBECTL_VERSION}/deb/Release.key" | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg && \
    chmod 644 /etc/apt/keyrings/kubernetes-apt-keyring.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v${KUBECTL_VERSION}/deb/ /" | tee /etc/apt/sources.list.d/kubernetes.list && \
    chmod 644 /etc/apt/sources.list.d/kubernetes.list && \
    apt-get update -y && \
    apt-get install -y kubectl && \
    ...
```

### 🪣 Installing the MinIO client 🪣

We're not done yet. Recently, I had to debug some MinIO-related issues, so I added
the [MinIO client](https://github.com/minio/mc) to the image. This is a simple download of the binary and copying it to
`/usr/local/bin`. But we need to make sure we download the correct version for the target architecture. This is where
the `TARGETARCH` build argument comes in handy.

```dockerfile
    ...
    # Install mc (MinIO Client) for the correct architecture
    MC_URL="https://dl.min.io/client/mc/release/linux-${TARGETARCH}/mc" && \
    curl -fsSL "$MC_URL" -o /usr/local/bin/mc && \
    chmod +x /usr/local/bin/mc && \
    ...
```

### 🐍 Installing Python packages 🐍

Next, we install some helpful Python packages. This is a simple `pip install` command. We use the `--no-cache-dir`
option to ensure pip installs the packages without caching the downloaded files, keeping the final Docker image smaller
and cleaner 🧼.

```dockerfile
    ...
    pip install --no-cache-dir \
      kubernetes \
      httpie \
      ipython && \
    ...  
```

The packages themselves are:

- `kubernetes` - the Python Kubernetes client, in case I want to run some Python scripts that access the K8s API
- `httpie` — a nicer `cURL` that I prefer
- `ipython` — a better Python shell

### 🔐 Creating a non-root user and final cleanup 🔐

Next, we create a non-root user to run the container. This is a good security practice. If an attacker escapes the
container due to some vulnerability, at least it won't run as root on the node. If you do need to run as root for
troubleshooting, just build a different debug image.

Finally, we clean up the APT cache and remove the package lists to reduce the image size and eliminate unnecessary
temporary files. While it may not be significant for large images, it's considered good practice and helps keep layers
lean and reproducible 📦.

```dockerfile
    ...
    # Create a non-root user
    useradd -m -s /bin/bash -u 1000 kuser && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
```

### 🧭 Setting workdir, user and command 🧭

The `WORKDIR` command sets the working directory for the container. This is where the container will start when it runs.
It doesn't matter much for a debug container, but it is a good practice to set it.

The `USER` command sets the user that will run the container — our non-root user.

Finally, the `CMD` command sets the default command to run when the container starts. In this case, we just want to
start a bash shell 🐚.

```dockerfile
WORKDIR /app
USER kuser
CMD ["bash"]
```

## 🏗️ The build.sh file 🏗️

OK. We have a Dockerfile. Now we need to build the image. The `build.sh` file is a simple script that builds the image
using Docker’s [`buildx`](https://docs.docker.com/reference/cli/docker/buildx/) command, which provides extended build
capabilities with [BuildKit](https://github.com/moby/buildkit).

There are two parts to the `build.sh` file. The first part creates a new builder if it doesn’t exist yet. It also
assigns the `VERSION` and `KUBECTL_VERSION` variables.

```bash
#!/bin/bash
set -e

VERSION=0.8
KUBECTL_VERSION=1.32

if ! docker buildx ls | grep -q "the-builder"; then
  docker buildx create --name the-builder --driver docker-container
fi
docker buildx use --builder the-builder
```

The second part actually builds the image. It uses `docker buildx build` to build for multiple platforms and sets
labels, build arguments, and image tags. Then it pushes the image to Docker Hub 🚀.

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --build-arg KUBECTL_VERSION="$KUBECTL_VERSION" \
  -t g1g1/py-kube:${VERSION} \
  -t g1g1/py-kube:latest \
  --label "org.opencontainers.image.created=$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
  --label "org.opencontainers.image.revision=$(git rev-parse HEAD)" \
  --label "org.opencontainers.image.licenses=MIT" \
  --push .

echo "Image successfully built and pushed as g1g1/py-kube:${VERSION} and g1g1/py-kube:latest"
```

## Building images in the CI/CD pipeline

Container images are best built in a CI/CD pipeline utilizing GitOps. This is a good practice because it ensures that
the images are built using a well-defined process whenever the relevant files change and don't depend on the discipline
of specific engineers.

The py-kube image may not relly need a CI/CD pipeline, but why not? We're already hosting the code on Github we may as
well define a simple Github Actions workflow to build the image and push it to Docker Hub. The pipeline is defined in
the `.github/workflows/build-py-kube.yml` file. It uses the `docker/build-push-action` action to build and push the
image.
As a bonus it also runs a [Trivy](https://trivy.dev/) scan on the image to check for vulnerabilities.

I will not go into too much detail here. Actually, I'll go into no detail whatsoever, as Github Actions 🐙🐱 deserve
their own blog post series. I'll just dump the workflow file here. Enjoy!

```yaml
name: Build and Push py-kube Image

on:
  push:
    paths:
      - 'py-kube/Dockerfile'
      - 'py-kube/.dockerignore'
    branches: [ main ]
  workflow_dispatch:

permissions:
  security-events: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to DockerHub
        uses: docker/login-action@v3
        with:
          username: g1g1
          password: ${{ secrets.DOCKERHUB_ACCESS_TOKEN }}

      - name: Get version from build.sh
        id: get_version
        run: |
          VERSION=$(grep ^VERSION= py-kube/build.sh | cut -d'=' -f2)
          echo "VERSION=$VERSION" >> "$GITHUB_OUTPUT"

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: ./py-kube
          file: ./py-kube/Dockerfile
          platforms: linux/amd64,linux/arm64
          push: true
          build-args: |
            BASE_IMAGE=python:3.13-slim@sha256:21e39cf1815802d4c6f89a0d3a166cc67ce58f95b6d1639e68a394c99310d2e5
            KUBECTL_VERSION=1.32
          tags: |
            g1g1/py-kube:${{ steps.get_version.outputs.VERSION }}
            g1g1/py-kube:latest
          labels: |
            org.opencontainers.image.created=${{ github.event.repository.updated_at }}
            org.opencontainers.image.revision=${{ github.sha }}
            org.opencontainers.image.licenses=MIT

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@7b7aa264d83dc58691451798b4d117d53d21edfe
        with:
          image-ref: docker.io/g1g1/py-kube:${{ steps.get_version.outputs.VERSION }}
          format: 'template'
          template: '@/contrib/sarif.tpl'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'

      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'
          ignore-unfixed: true
```

## 🐘 The Elephants in the Room 🐘

Let’s talk about some elephants. Why not use a [Distroless](https://github.com/GoogleContainerTools/distroless) image?
Why not use [Buildpacks](https://buildpacks.io)? Why not use [Kaniko](https://github.com/GoogleContainerTools/kaniko)?
Why not use multistage builds?

The short answer is: this is a debug image, not a production microservice 🏭. It’s meant to be interactive, flexible,
and it's fine if it's a little heavy. Distroless images are great for minimal, secure containers — but they don’t even
include a shell. That’s a no-go for debugging.

Buildpacks are great for abstracting builds. But I want control over what goes into this image — including low-level
tools like `mc`, `kubectl`, and `netcat`.

Kaniko is great for in-cluster builds. But I’m building locally or using Github Actions and pushing to Docker Hub, so
BuildKit via `buildx` is
just easier.

Multistage builds are awesome when you want to build the image in a rich environment with all kind of tools and generate
a tight image based on a spartan base image like SCRATCH or Distroless with only the final artifact. But this is a debug
image. The goal is to have all the tools available when I `kubectl exec` into a pod 🛠️.

## 🏡 Take home points 🏡

- Understanding how to build efficient and secure images is essential
- Debug images have very different requirements than production images
- Always scan your images for vulnerabilities

🇦🇫 خداحافظ دوستان من
