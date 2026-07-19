# main.py
from pathlib import Path
from strands import Agent, tool
from strands.models.bedrock import BedrockModel
from botocore.exceptions import ClientError
import boto3
import json
from datetime import datetime, timezone
from bedrock_agentcore.runtime import BedrockAgentCoreApp

# ====================== LOAD SYSTEM PROMPT ======================

def load_system_prompt(prompt_path: str = "prompt.md") -> str:
    """Load system prompt from markdown file using pathlib."""
    prompt_file = Path(prompt_path)
    
    if not prompt_file.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {prompt_file.absolute()}\n"
            f"Please create a file named '{prompt_path}' in the project root."
        )
    
    try:
        return prompt_file.read_text(encoding="utf-8").strip()
    except Exception as e:
        raise RuntimeError(f"Error reading prompt file {prompt_file}: {e}")

# ====================== CUSTOM AWS TOOLS ======================

region_default = "eu-central-1"

@tool
def list_volumes(region: str = region_default, filters: list = None) -> str:
    """List EC2 volumes."""
    try:
        ec2 = boto3.client('ec2', region_name=region)
        params = {}
        if filters:
            params["Filters"] = filters
        response = ec2.describe_volumes(**params)

        volumes = []
        for vol in response.get('Volumes', []):
            name = next((tag['Value'] for tag in vol.get('Tags', []) if tag['Key'] == 'Name'), 'No Name')
            tags_dict = {tag['Key']: tag['Value'] for tag in vol.get('Tags', [])}
            volumes.append({
                "VolumeId": vol['VolumeId'],
                "Size": vol['Size'],
                "State": vol['State'],
                "VolumeType": vol['VolumeType'],
                "Name": name,
                "Tags": tags_dict,
                "CreateTime": str(vol['CreateTime'])
            })
        return json.dumps(volumes, indent=2, default=str)
    except Exception as e:
        return f"Error listing volumes in {region}: {str(e)}"

@tool
def delete_volume(volume_id: str, region: str = region_default) -> str:
    """Delete an EC2 volume. Use with caution!"""
    try:
        ec2 = boto3.client('ec2', region_name=region)
        ec2.delete_volume(VolumeId=volume_id)
        return f"✅ Volume {volume_id} has been successfully deleted in {region}."
    except ClientError as e:
        return f"❌ Error deleting volume in {region}: {e}"

@tool
def list_snapshots(region: str = region_default, filters: list = None) -> str:
    """List EC2 snapshots."""
    try:
        ec2 = boto3.client('ec2', region_name=region)
        params = {"OwnerIds": ["self"]}
        if filters:
            params["Filters"] = filters
        response = ec2.describe_snapshots(**params)

        snapshots = []
        for snap in response.get('Snapshots', []):
            name = next((tag['Value'] for tag in snap.get('Tags', []) if tag['Key'] == 'Name'), 'No Name')
            tags_dict = {tag['Key']: tag['Value'] for tag in snap.get('Tags', [])}
            snapshots.append({
                "SnapshotId": snap['SnapshotId'],
                "VolumeId": snap.get('VolumeId'),
                "State": snap['State'],
                "StartTime": str(snap['StartTime']),
                "Description": snap.get('Description', ''),
                "Name": name,
                "Tags": tags_dict
            })
        return json.dumps(snapshots, indent=2, default=str)
    except Exception as e:
        return f"Error listing snapshots in {region}: {str(e)}"

@tool
def delete_snapshot(snapshot_id: str, region: str = region_default) -> str:
    """Delete an EC2 snapshot. Use with caution!"""
    try:
        ec2 = boto3.client('ec2', region_name=region)
        ec2.delete_snapshot(SnapshotId=snapshot_id)
        return f"✅ Snapshot {snapshot_id} has been successfully deleted in {region}."
    except ClientError as e:
        return f"❌ Error deleting snapshot in {region}: {e}"

@tool
def find_old_resources(region: str = region_default, min_age_days: int = 30) -> str:
    """Find EC2 volumes and snapshots older than a given number of days."""
    try:
        ec2 = boto3.client('ec2', region_name=region)
        now = datetime.now(timezone.utc)

        vol_response = ec2.describe_volumes()
        old_volumes = []
        for vol in vol_response.get('Volumes', []):
            age_days = (now - vol['CreateTime']).days
            if age_days < min_age_days:
                continue
            name = next((tag['Value'] for tag in vol.get('Tags', []) if tag['Key'] == 'Name'), 'No Name')
            tags_dict = {tag['Key']: tag['Value'] for tag in vol.get('Tags', [])}
            old_volumes.append({
                "VolumeId": vol['VolumeId'],
                "Size": vol['Size'],
                "State": vol['State'],
                "VolumeType": vol['VolumeType'],
                "Name": name,
                "Tags": tags_dict,
                "CreateTime": str(vol['CreateTime']),
                "AgeDays": age_days
            })

        snap_response = ec2.describe_snapshots(OwnerIds=["self"])
        old_snapshots = []
        for snap in snap_response.get('Snapshots', []):
            age_days = (now - snap['StartTime']).days
            if age_days < min_age_days:
                continue
            name = next((tag['Value'] for tag in snap.get('Tags', []) if tag['Key'] == 'Name'), 'No Name')
            tags_dict = {tag['Key']: tag['Value'] for tag in snap.get('Tags', [])}
            old_snapshots.append({
                "SnapshotId": snap['SnapshotId'],
                "VolumeId": snap.get('VolumeId'),
                "State": snap['State'],
                "StartTime": str(snap['StartTime']),
                "Description": snap.get('Description', ''),
                "Name": name,
                "Tags": tags_dict,
                "AgeDays": age_days
            })

        result = {
            "Region": region,
            "MinAgeDaysFilter": min_age_days,
            "OldVolumeCount": len(old_volumes),
            "OldVolumes": old_volumes,
            "OldSnapshotCount": len(old_snapshots),
            "OldSnapshots": old_snapshots
        }
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return f"Error finding old resources in {region}: {str(e)}"

# ====================== AGENT ======================

model = BedrockModel(
    #model_id="eu.anthropic.claude-sonnet-4-20250514-v1:0"  # Updated to valid Bedrock model ID
    model_id="eu.anthropic.claude-sonnet-4-6"
)

agent = Agent(
    model=model,
    tools=[list_volumes, delete_volume, list_snapshots, delete_snapshot, find_old_resources],
    system_prompt=load_system_prompt(),   # Loaded from prompt.md  
)
# ====================== AGENTCORE RUNTIME WRAPPER ======================

app = BedrockAgentCoreApp()

@app.entrypoint
def agent_invocation(payload, context):
    """Handler for agent invocation - required for AgentCore Runtime"""
    print(f"Context: {context}")

    # Extract prompt from payload
    user_message = payload.get("prompt", "No prompt found in input. Please provide a 'prompt' key in your JSON payload.")
    print(f"Received prompt: {user_message}")

    # Execute agent
    result = agent(user_message)
    print(f"Agent result: {result}")

    # Return structured response
    return {
        "result": result.message,
        "metadata": {
            "session_id": getattr(context, 'session_id', 'unknown'),
            "actor_id": getattr(context, 'actor_id', 'unknown')
        }
    }

# This is required for containerized deployment
if __name__ == "__main__":
    print(f"Agent is running...on port 8080.")
    app.run()
