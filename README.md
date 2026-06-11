# 🛠️ AWS EC2 Volumes & Snapshots Management Agent

> An intelligent, safety-first AWS assistant powered by Amazon Bedrock (Claude Sonnet) that helps you manage EC2 volumes and snapshots through natural language conversations.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![AWS](https://img.shields.io/badge/AWS-Bedrock-orange.svg)](https://aws.amazon.com/bedrock/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 Overview

This Python application builds a specialized AI agent using the **strands** framework. The agent acts as an experienced AWS Senior Cloud Engineer and can only perform a strictly limited set of safe operations on EC2 volumes and snapshots.

It is designed for **cleanup and housekeeping** of unused resources with strong safety guardrails (especially around deletions).

## ✨ Key Features

- **List Volumes** — Detailed view of EC2 volumes including Name tag, size, state, type, and creation time
- **Safe Volume Deletion** — Only deletes volumes that are:
  - In `available` state
  - Not attached to any EC2 instance
- **Double Confirmation** on every delete operation
- **List Snapshots** — Shows all snapshots owned by your AWS account
- **Snapshot Deletion** with confirmation
- **Markdown Reports** — Automatically generates clean tables summarizing deleted resources
- **Fun Personality** — Helpful, technical, with a light "Cookie Monster in AWS" vibe

## 📋 Prerequisites

- Python 3.10 or higher
- AWS account with **Amazon Bedrock** access enabled in `eu-central-1`
- IAM user/role with the following permissions:
  - `ec2:DescribeVolumes`
  - `ec2:DeleteVolume`
  - `ec2:DescribeSnapshots`
  - `ec2:DeleteSnapshot`
- AWS credentials configured (via `aws configure`, environment variables, or IAM role)

## 🛠️ Installation

```bash
# 1. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # Linux/Mac
# venv\Scripts\activate    # Windows

# 2. Install dependencies
pip install strands boto3
```

> **Note:** The `strands` package provides the `Agent` and `@tool` decorator used in this project.

## ▶️ How to Run

```bash
python aws_agent.py
```

You will see:

```
🚀 Agent ready - volumes and snapshots management.
Available commands: list volumes, delete volumes, list snapshots, delete snapshots.
If you want to exit, type: exit

You: 
```

### Example Conversation

```
You: list all my volumes

You: delete volume vol-0a1b2c3d4e5f67890

Agent: I see volume vol-0a1b2c3d4e5f67890 is in 'available' state and not attached.
       This action is irreversible. Do you want me to proceed with deletion? (yes/no)

You: yes

Agent: Confirming one more time — you want to permanently delete volume vol-0a1b2c3d4e5f67890? (yes/no)

You: yes

Agent: ✅ Volume vol-0a1b2c3d4e5f67890 has been successfully deleted.

       ### Deletion Report

       | Resource Type | Resource ID          | Status    |
       |---------------|----------------------|-----------|
       | Volume        | vol-0a1b2c3d4e5f67890 | Deleted   |
```

Type `exit` or `quit` to leave the interactive session.

## 🧰 Available Tools

| Tool                | Description                                                                 | Safety Rules                          |
|---------------------|-----------------------------------------------------------------------------|---------------------------------------|
| `list_volumes`      | Lists EC2 volumes with tags, size, state, type and creation time           | Read-only                             |
| `delete_volume`     | Deletes a single volume                                                     | Only `available` + unattached volumes |
| `list_snapshots`    | Lists snapshots owned by you (`OwnerIds: self`)                             | Read-only                             |
| `delete_snapshot`   | Deletes a snapshot                                                          | Requires double confirmation          |

All tools return human-readable output (JSON for lists, success/error messages for deletions).

## 🤖 Agent Configuration

The agent is powered by:

```python
model = BedrockModel(model_id="eu.anthropic.claude-sonnet-4-6")
```

### Core Rules (from system prompt)

- Only allowed actions: **list volumes**, **delete volumes** (safe only), **list snapshots**, **delete snapshots**, and **generate markdown reports**
- **Region is fixed** to `eu-central-1`
- Must **confirm every deletion twice** before executing
- Respond in short, technical, merit-based style with a touch of fun
- Never perform any other AWS actions

## ⚠️ Safety & Limitations

- The agent **will refuse** to delete volumes that are in-use or attached to instances
- All delete operations require explicit double confirmation
- The current implementation hardcodes `region_default = "eu-central-1"` (the `region` parameter in tools is accepted but not yet used)
- This tool is intended **only for cleanup of unused resources**
- Always double-check resource IDs before confirming deletion

## 📁 Project Structure

```
.
├── aws_agent.py          # Main interactive agent script
├── README.md             # This documentation
└── requirements.txt      # (optional) pip dependencies
```

## 🔧 Customization Ideas

- Change the default region at the top of `aws_agent.py`
- Extend the agent with more tools (e.g. create snapshots, list instances)
- Adjust the system prompt to change tone or add new rules
- Add logging or audit trail for all delete operations
- Integrate with Slack / Microsoft Teams for team usage

## 📝 License

This project is provided as-is for educational and internal tooling purposes.

---

**Built with ❤️ and a healthy respect for AWS costs.**

*Cookie Monster says: "Me want to delete only unused volumes... and maybe a cookie."* 🍪
