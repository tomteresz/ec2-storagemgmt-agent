from strands import Agent, tool
from strands.models.bedrock import BedrockModel
import boto3
from botocore.exceptions import ClientError
import json

# ====================== CUSTOM AWS TOOLS ======================

region_default = "eu-central-1"

@tool
def list_volumes(region: str = "region_default", filters: dict = None) -> str:
    """List EC2 volumes.
    Args:
        region: AWS region (default: region_default)
        filters: Optional filters (e.g. {"Name": "status", "Values": ["available"]})
    """
    try:
        ec2 = boto3.client('ec2', region_name=region_default)
        params = {}
        if filters:
            params["Filters"] = filters
        response = ec2.describe_volumes(**params)
        
        volumes = []
        for vol in response.get('Volumes', []):
            name = next((tag['Value'] for tag in vol.get('Tags', []) if tag['Key'] == 'Name'), 'No Name')
            volumes.append({
                "VolumeId": vol['VolumeId'],
                "Size": vol['Size'],
                "State": vol['State'],
                "VolumeType": vol['VolumeType'],
                "Name": name,
                "CreateTime": str(vol['CreateTime'])
            })
        return json.dumps(volumes, indent=2, default=str)
    except Exception as e:
        return f"Error listing volumes: {str(e)}"


@tool
def delete_volume(volume_id: str, region: str = "region_default") -> str:
    """Delete an EC2 volume. Use with caution!
    Args:
        volume_id: ID od the volume to delete
        region: region_default
    """
    try:
        ec2 = boto3.client('ec2', region_name=region_default)
        ec2.delete_volume(VolumeId=volume_id)
        return f"✅ Volume {volume_id} has been sucessfully deleted."
    except ClientError as e:
        return f"❌ Error deleting volume: {e}"


@tool
def list_snapshots(region: str = "region_default", filters: dict = None) -> str:
    """List EC2 snapshots.
    Args:
        region: region_default
        filters: Optional filters
    """
    try:
        ec2 = boto3.client('ec2', region_name=region_default)
        
        params = {"OwnerIds": ["self"]}   # ← Added this line (correct way)
        
        if filters:
            params["Filters"] = filters

        response = ec2.describe_snapshots(**params)
        
        snapshots = []
        for snap in response.get('Snapshots', []):
            name = next((tag['Value'] for tag in snap.get('Tags', []) if tag['Key'] == 'Name'), 'No Name')
            snapshots.append({
                "SnapshotId": snap['SnapshotId'],
                "VolumeId": snap.get('VolumeId'),
                "State": snap['State'],
                "StartTime": str(snap['StartTime']),
                "Description": snap.get('Description', ''),
                "Name": name
            })
        return json.dumps(snapshots, indent=2, default=str)
    except Exception as e:
        return f"Error listing snapshots: {str(e)}"


@tool
def delete_snapshot(snapshot_id: str, region: str = "region_default") -> str:
    """Delete an EC2 snapshot. Use with caution!
    Args:
        snapshot_id: ID of the snapshot to delete
        region: region_default
    """
    try:
        ec2 = boto3.client('ec2', region_name=region_default)
        ec2.delete_snapshot(SnapshotId=snapshot_id)
        return f"✅ Snapshot {snapshot_id} został usunięty pomyślnie."
    except ClientError as e:
        return f"❌ Error deleting snapshot: {e}"


# ====================== AGENT ======================

model = BedrockModel(
    model_id="eu.anthropic.claude-sonnet-4-6"
)

agent = Agent(
    model=model,
    tools=[list_volumes, delete_volume, list_snapshots, delete_snapshot],
    system_prompt="""
    
You are helpful AWS assistant with 10 years experience as AWS Senior Cloud Engineer in Fortune500 companies. 

DO NOT take ANY actions in Amazon AWS except following on the list:

1) list volumes
2) delete volumes but only those with following parameters:
    -   volume state = available
    -   not attached to any resources
3) list snapshots
4) delete snapshots
5) create report table in markdown with info about deleted volumes/snapshots

Region: eu-central-1

Anwser in short, technical, merit-based, but satisfying way. You could be a bit like Cookie Monster in AWS. Let's make a tool funny a bit.

Always confirm delete operation. Confirm deletion two times before execution - inform the user about that before execution."""
)

if __name__ == "__main__":
    print("🚀 Agent ready - volumes and snapshots management.")
    print("Available commands: list volumes, delete volumes, list snapshots, delete snapshots.")
    print("If you want to exit, type: exit")
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        response = agent(user_input)
        #print(f"\nAgent: {response}")
