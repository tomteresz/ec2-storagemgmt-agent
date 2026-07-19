# 🛠️ AWS EC2 Volumes & Snapshots Management Agent

> An intelligent, safety-first AWS assistant powered by Amazon Bedrock (Claude Sonnet) that helps you manage EC2 volumes and snapshots through natural language conversations, deployed as an **Amazon Bedrock AgentCore Runtime** HTTP service.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![AWS](https://img.shields.io/badge/AWS-Bedrock-orange.svg)](https://aws.amazon.com/bedrock/)
[![AWS](https://img.shields.io/badge/AWS-AgentCore-orange.svg)](https://aws.amazon.com/bedrock/agentcore/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 Overview

This Python application builds a specialized AI agent using the **Strands Agents** framework, wrapped and served through **Amazon Bedrock AgentCore Runtime** (`bedrock_agentcore.runtime.BedrockAgentCoreApp`) as a containerized HTTP microservice listening on port `8080`. The agent acts as an experienced AWS Senior Cloud Engineer and can only perform a strictly limited set of safe operations on EC2 volumes and snapshots.

It is designed for **cleanup and housekeeping** of unused resources with strong safety guardrails (especially around deletions). Default region is `eu-central-1`, but any AWS region can be specified.

Unlike a simple local CLI script, the agent is exposed via a single HTTP endpoint (`POST /invocations`) that accepts a JSON payload with a `prompt` key and returns a structured JSON response, making it deployable behind Amazon Bedrock AgentCore Runtime infrastructure.

## ✨ Key Features

- **List Volumes** — Detailed view of EC2 volumes including Name tag, size, state, type, tags, and creation time (optional filters)
- **Safe Volume Deletion** — Only deletes volumes that are:
  - In `available` state
  - Not attached to any EC2 instance
- **Double Confirmation** on every delete operation (YES/NO twice)
- **List Snapshots** — Shows all snapshots owned by your AWS account (`OwnerIds: self`)
- **Snapshot Deletion** with double confirmation
- **Find Old Resources** — Flags volumes and snapshots older than N days (default: 30)
- **Markdown Reports** — Generates clean tables summarizing volumes and/or snapshots (including multi-region style reports)
- **Multi-region** — Tools accept a `region` parameter; user can specify e.g. `eu-west-1`, `us-east-1`
- **Fun Personality** — Helpful, technical, with a light "Cookie Monster in AWS" vibe
- **AgentCore Runtime Wrapper** — Agent is exposed as an HTTP service via `BedrockAgentCoreApp`, ready for containerized deployment and invocation through `/invocations`

## 📋 Prerequisites

- Python 3.10 or higher
- AWS account with **Amazon Bedrock** access enabled (model: `eu.anthropic.claude-sonnet-4-6`)
- IAM user/role with the following permissions:
  - `ec2:DescribeVolumes`
  - `ec2:DeleteVolume`
  - `ec2:DescribeSnapshots`
  - `ec2:DeleteSnapshot`
- AWS credentials configured (via `aws configure`, environment variables, or IAM role)
- Bedrock model access for Claude Sonnet in the relevant inference profile / region
- `jq` and `curl` installed locally (used by `runit.sh` to send requests and parse responses)
- (For containerized/AgentCore deployment) The `bedrock-agentcore` Python package, which provides `bedrock_agentcore.runtime.BedrockAgentCoreApp`

## 🛠️ Installation

```bash
# 1. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # Linux/Mac
# venv\Scripts\activate    # Windows

# 2. Install dependencies
pip install -r requirements.txt
```

> **Note:** The `strands-agents` package provides `Agent`, `@tool`, and `BedrockModel`. Import path used in the script: `from strands import Agent, tool` and `from strands.models.bedrock import BedrockModel`. The `bedrock-agentcore` package provides `BedrockAgentCoreApp`, imported as `from bedrock_agentcore.runtime import BedrockAgentCoreApp`.

Content of `requirements.txt` (update to include the AgentCore SDK):

```
strands-agents 
strands-agents-tools
boto3
bedrock-agentcore
```

## ▶️ How to Run

The agent no longer runs as an interactive terminal chat — it starts an HTTP server on port `8080` and waits for requests at the `/invocations` endpoint:

```bash
python main.py
```

You will see:

```
Agent is running...on port 8080.
```

### Sending a Prompt

Use the included `runit.sh` helper script to send a prompt to the running agent:

```bash
chmod +x runit.sh
./runit.sh -prompt "list all my volumes"
```

`runit.sh` builds a JSON payload with `jq`, `POST`s it to `http://localhost:8080/invocations`, and extracts the text response with `jq -r '.result.content[0].text'`.

### Example Conversation

```
./runit.sh -prompt "find old resources older than 60 days in eu-central-1"

./runit.sh -prompt "delete volume vol-0a1b2c3d4e5f67890"

Agent: I see volume vol-0a1b2c3d4e5f67890 is in 'available' state and not attached.
       This action is irreversible. Do you want me to proceed with deletion? (yes/no)

./runit.sh -prompt "yes"

Agent: Confirming one more time — you want to permanently delete volume vol-0a1b2c3d4e5f67890? (yes/no)

./runit.sh -prompt "yes"

Agent: ✅ Volume vol-0a1b2c3d4e5f67890 has been successfully deleted in eu-central-1.

       ### Deletion Report

       | Resource Type | Resource ID           | Region       | Status  |
       |---------------|-----------------------|--------------|---------|
       | Volume        | vol-0a1b2c3d4e5f67890 | eu-central-1 | Deleted |
```

> ⚠️ Note: Because the runtime is stateless per HTTP request (no local session/conversation loop), multi-turn confirmation flows depend on how session/state is managed by the AgentCore Runtime session (`context.session_id`) rather than an in-process REPL loop.

Stop the server with `Ctrl+C` in the terminal running `python main.py`. There is no `exit`/`quit` command inside `runit.sh` — simply stop sending requests.

### Screenshot of the agent running

![](agent_running.png?raw=true)

## 🧰 Available Tools

| Tool                 | Description                                                                 | Safety Rules                                      |
|----------------------|-----------------------------------------------------------------------------|---------------------------------------------------|
| `list_volumes`       | Lists EC2 volumes (Name, size, state, type, tags, CreateTime). Optional filters | Read-only                                         |
| `delete_volume`      | Deletes a single volume by ID                                               | Agent only allows `available` + unattached volumes; double confirm |
| `list_snapshots`     | Lists snapshots owned by you (`OwnerIds: self`). Optional filters           | Read-only                                         |
| `delete_snapshot`    | Deletes a snapshot by ID                                                    | Double confirmation required                      |
| `find_old_resources` | Finds volumes & snapshots older than `min_age_days` (default 30)            | Read-only; returns age in days                    |

All tools accept an optional `region` argument (default: `eu-central-1`). List tools return JSON; delete tools return success/error messages.

Note: in the current implementation, `delete_volume` and `delete_snapshot` catch only `botocore.exceptions.ClientError`, while the list/find tools use a broader `except Exception`; unexpected non-`ClientError` exceptions in delete calls would propagate rather than return a formatted error string.

### Tool signatures (summary)

```python
list_volumes(region="eu-central-1", filters=None)
delete_volume(volume_id, region="eu-central-1")
list_snapshots(region="eu-central-1", filters=None)
delete_snapshot(snapshot_id, region="eu-central-1")
find_old_resources(region="eu-central-1", min_age_days=30)
```

Filter example for volumes:

```python
[{"Name": "status", "Values": ["available"]}]
```

## 🤖 Agent Configuration

The agent is powered by:

```python
model = BedrockModel(
    #model_id="eu.anthropic.claude-sonnet-4-20250514-v1:0"  # Updated to valid Bedrock model ID
    model_id="eu.anthropic.claude-sonnet-4-6"
)
```

> The commented-out line shows a prior model ID (`eu.anthropic.claude-sonnet-4-20250514-v1:0`) that was replaced with `eu.anthropic.claude-sonnet-4-6`; keep this in mind if you need to roll back or troubleshoot inference profile access issues.

Default region constant:

```python
region_default = "eu-central-1"
```

### Core Rules (from system prompt)

- **Allowed actions only:**
  1. List volumes  
  2. Delete volumes — only if state = `available` and not attached  
  3. List snapshots  
  4. Delete snapshots  
  5. Find EC2 volumes and snapshots older than N days (default: 30)  
  6. Create markdown report/table for volumes and/or snapshots (including all-regions style reports)
- User may specify any AWS region (`eu-central-1`, `eu-west-1`, `us-east-1`, etc.)
- **Confirm every deletion twice** (YES/NO) before execution; inform the user beforehand
- Short, technical, merit-based answers with a light Cookie Monster–in–AWS tone
- Refuse any other questions or AWS actions outside the list above

### AgentCore Runtime Wrapper

The Strands `agent` object is wrapped by `BedrockAgentCoreApp` for deployment as a Runtime-compatible HTTP service:

```python
app = BedrockAgentCoreApp()

@app.entrypoint
def agent_invocation(payload, context):
    """Handler for agent invocation - required for AgentCore Runtime"""
    user_message = payload.get("prompt", "No prompt found in input. Please provide a 'prompt' key in your JSON payload.")
    result = agent(user_message)
    return {
        "result": result.message,
        "metadata": {
            "session_id": getattr(context, "session_id", "unknown"),
            "actor_id": getattr(context, "actor_id", "unknown")
        }
    }

if __name__ == "__main__":
    app.run()
```

- `payload` must contain a `prompt` key; if missing, a default error string is returned instead of raising an exception.
- `context.session_id` and `context.actor_id` are read via `getattr` with an `"unknown"` fallback, so the handler tolerates a `context` object that doesn't define these attributes.
- The service listens on port `8080` by default (`app.run()`), matching the port used in `runit.sh`.

## ⚠️ Safety & Limitations

- The agent **must refuse** to delete volumes that are in-use or attached to instances
- All delete operations require **explicit double confirmation**
- Deletion is irreversible — always verify resource IDs
- Snapshots listed are limited to those owned by the account (`OwnerIds: ["self"]`)
- `find_old_resources` uses volume `CreateTime` and snapshot `StartTime` in UTC
- Intended **only for cleanup of unused resources**
- Ensure Bedrock model access and EC2 permissions are correctly scoped in your account
- Because the agent is now served over HTTP via AgentCore Runtime, ensure the `/invocations` endpoint is not exposed to untrusted networks without additional authentication/authorization in front of it
- `delete_volume`/`delete_snapshot` only catch `ClientError`; other unexpected exceptions will propagate up through the HTTP handler

## 📁 Project Structure

```
.
├── main.py               # Main agent script + AgentCore Runtime HTTP wrapper (entrypoint: agent_invocation)
├── runit.sh              # Helper script to POST prompts to the running agent via curl/jq
├── README.md             # This documentation
├── agent_running.png     # Optional screenshot
└── requirements.txt      # pip dependencies (strands-agents, strands-agents-tools, boto3, bedrock-agentcore)
```

## 🔧 Customization Ideas

- Change `region_default` at the top of `main.py`
- Add filters or extra fields to list/find tools (e.g. encrypted, IOPS, storage tier)
- Extend with create-snapshot, tag management, or Cost Explorer cost estimates
- Adjust the system prompt for tone, extra guardrails, or multi-account support
- Add logging / audit trail for all delete operations
- Integrate with Slack / Microsoft Teams for team usage
- Wire `find_old_resources` into scheduled cleanup workflows (still keep human confirmation for deletes)
- Add authentication/authorization in front of the `/invocations` endpoint before exposing it beyond localhost
- Harden `delete_volume`/`delete_snapshot` error handling to also catch generic `Exception`, matching the list/find tools

## 📝 License

This project is provided as-is for educational and internal tooling purposes.

---

**Built with ❤️ and a healthy respect for AWS costs.**

*Cookie Monster says: "Me want to delete only unused volumes... and maybe a cookie."* 🍪
