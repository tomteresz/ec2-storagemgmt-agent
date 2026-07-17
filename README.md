# 🛠️ AWS EC2 Volumes & Snapshots Management Agent

> An intelligent, safety-first AWS assistant powered by Amazon Bedrock (Claude Sonnet) that helps you manage EC2 volumes and snapshots through natural language conversations.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![AWS](https://img.shields.io/badge/AWS-Bedrock-orange.svg)](https://aws.amazon.com/bedrock/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 Overview

This Python application builds a specialized AI agent using the **Strands Agents** framework. The agent acts as an experienced AWS Senior Cloud Engineer and can only perform a strictly limited set of safe operations on EC2 volumes and snapshots **across multiple regions**.

It is designed for **cleanup and housekeeping** of unused resources with strong safety guardrails (especially around deletions).

---

## ✨ Key Features

- **Multi-Region Support** — Works in any AWS region (user can specify)
- **List Volumes** — Detailed view including Name tag, all tags, size, state, type, and creation time
- **Safe Volume Deletion** — Only deletes volumes that are:
  - In `available` state
  - Not attached to any EC2 instance
- **Double Confirmation** on every delete operation
- **List Snapshots** — Shows all snapshots owned by your account
- **Snapshot Deletion** with confirmation
- **Markdown Reports** — Automatically generates clean tables summarizing deleted resources across regions
- **Fun Personality** — Helpful, technical, with a light "Cookie Monster in AWS" vibe
- **Colored Terminal Output** — Green prompt for better readability

---

## 📋 Prerequisites

- Python 3.10 or higher
- AWS account with **Amazon Bedrock** access enabled
- IAM user/role with the following permissions:
  - `ec2:DescribeVolumes`
  - `ec2:DeleteVolume`
  - `ec2:DescribeSnapshots`
  - `ec2:DeleteSnapshot`
- AWS credentials configured (via `aws configure`, environment variables, or IAM role)

---

## 🛠️ Installation

```bash
# 1. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # Linux/Mac
# venv\Scripts\activate    # Windows

# 2. Install dependencies
pip install -r requirements.txt
```

**`requirements.txt`**
```txt
strands-agents
strands-agents-tools
boto3
```

---

## ▶️ How to Run

```bash
python agent.py
```

You will see:

```
🚀 Agent ready - volumes and snapshots management.
Available commands: list volumes, delete volumes, list snapshots, delete snapshots, create ebs report. Say hello.
If you want to exit, type: exit or quit

You: 
```

### Example Conversation

```
You: list volumes in eu-west-1

You: list volumes, filter: available only

You: delete volume vol-0a1b2c3d4e5f67890 in us-east-1
```

---

## 🧰 Available Tools

| Tool                | Description                                                                 | Safety Rules                          |
|---------------------|-----------------------------------------------------------------------------|---------------------------------------|
| `list_volumes`      | Lists EC2 volumes with full tags, size, state, type and creation time      | Read-only                             |
| `delete_volume`     | Deletes a single volume                                                     | Only `available` + unattached volumes |
| `list_snapshots`    | Lists snapshots owned by you                                                | Read-only                             |
| `delete_snapshot`   | Deletes a snapshot                                                          | Requires double confirmation          |

All tools support the `region` parameter and return human-readable output.

---

## 🤖 Agent Configuration

The agent is powered by:

```python
model = BedrockModel(model_id="eu.anthropic.claude-sonnet-4-6")
```

### Core Rules (from system prompt)

- Can work in **any AWS region** (user can specify)
- Only allowed actions: **list volumes**, **delete volumes** (safe only), **list snapshots**, **delete snapshots**, and **generate markdown reports**
- Must **confirm every deletion twice** before executing
- Respond in short, technical, merit-based style with a touch of fun
- Never perform any other AWS actions

---

## ⚠️ Safety & Limitations

- The agent **will refuse** to delete volumes that are in-use or attached to instances
- All delete operations require explicit double confirmation
- Intended **only for cleanup of unused resources**
- Always double-check resource IDs and region before confirming deletion

---

## 📁 Project Structure

```
.
├── agent.py                # Main interactive agent script
├── requirements.txt
└── README.md               # This documentation
```

---

## 🔧 Customization Ideas

- Extend the agent with more tools (e.g. create snapshots, list instances, cost reporting)
- Adjust the system prompt to change tone or add new rules
- Add logging or audit trail for all delete operations

---

**Built with ❤️ and a healthy respect for AWS costs.**

*Cookie Monster says: "Me want to delete only unused volumes... and maybe a cookie."* 🍪
