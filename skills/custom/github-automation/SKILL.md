---
name: github-automation
description: Reusable workflow for setting up GitHub repositories, configuring CI/CD pipelines for DigitalOcean droplets, adding revvel-standards documentation, and establishing a self-healing monitor. Use this skill when a user asks to set up a new project repository, configure auto-deployments, or apply the standard S.H.I.F.T. monitor to a new or existing app.
---

# GitHub Automation & CI/CD Setup

This skill provides the standard workflow for initializing a new project repository, configuring a CI/CD pipeline to a DigitalOcean droplet, and setting up the S.H.I.F.T. self-healing monitor.

## Workflow Overview

When setting up a new application or applying standards to an existing one, follow these steps in order:

1. **Repository Setup**: Create or configure the GitHub repository.
2. **CI/CD Pipeline**: Generate and push the `deploy.yml` workflow and `deploy.sh` script.
3. **Secret Configuration**: Set up the `SSH_PRIVATE_KEY` for deployment.
4. **S.H.I.F.T. Monitor**: Add the self-healing monitor workflow and tests.
5. **Documentation**: Add the mandatory `MANUS_INSTRUCTIONS.md` and update the `HANDOFF.md`.

## Step 1: Repository Setup

If the repository does not exist, create it using the GitHub CLI:

```bash
gh repo create <repo-name> --private
```

Ensure the repository is cloned locally and you are working on the `main` branch.

## Step 2: CI/CD Pipeline Configuration

Every application must have an automated deployment pipeline. Use the `bootstrap-deploy.sh` script from the `revvel-standards` repository to generate the necessary files:

```bash
curl -sL https://raw.githubusercontent.com/midnghtsapphire/revvel-standards/main/templates/cicd/bootstrap-deploy.sh | bash -s <app_name> <droplet_ip> <app_dir>
```

This will create:
- `.github/workflows/deploy.yml` (The automated GitHub Actions workflow)
- `deploy.sh` (A manual fallback deployment script)

## Step 3: Secret Configuration

The CI/CD pipeline requires an SSH key to connect to the DigitalOcean droplet. Since the user's account is a personal account (not an organization), this secret must be set per repository.

Instruct the user to run the following command from their local machine (where the private key resides):

```bash
gh secret set SSH_PRIVATE_KEY --repo midnghtsapphire/<repo-name> < ~/.ssh/growlingeyes_deploy
```

*Note: Do not attempt to generate or manage this key within the sandbox unless explicitly requested. Rely on the user to provide the existing shared key.*

## Step 4: S.H.I.F.T. Monitor Setup

To ensure the application remains highly available and resilient, apply the S.H.I.F.T. self-healing monitor:

1. Copy the `monitor.yml` template from `revvel-standards/templates/cicd/monitor.yml` to `.github/workflows/monitor.yml` in the project repository.
2. Instruct the user to add the `LIVE_URL` repository variable (e.g., `https://growlingeyes.com`).

This monitor runs every 10 minutes, checks the live site, and automatically restarts the application via SSH if it detects a failure (e.g., HTTP 502).

## Step 5: Documentation Standards

Every project must adhere to the `revvel-standards` documentation requirements:

1. **`MANUS_INSTRUCTIONS.md`**: Create or copy this file into the `docs/` directory. It must contain the build specifications, data sources, and success criteria.
2. **`HANDOFF.md`**: Ensure this file exists and includes the "Infrastructure Location & Architecture Tracking" table (Live URL, Droplet IP, App Directory, GitHub Repo).

## Finalizing the Setup

Once all files are generated and configured, commit and push them to the `main` branch:

```bash
git add .
git commit -m "chore: setup CI/CD pipeline and S.H.I.F.T. monitor"
git push origin main
```

Inform the user that the pipeline is live and remind them of any manual steps required (e.g., setting the `SSH_PRIVATE_KEY` secret).
