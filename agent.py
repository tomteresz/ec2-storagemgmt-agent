from strands import Agent, tool
from strands.models.bedrock import BedrockModel
from botocore.exceptions import ClientError
import boto3
import json
from datetime import datetime, timezone


# ====================== CUSTOM AWS TOOLS ======================

region_default = "eu-central-1"

@tool
def list_volumes(region: str = region_default, filters: list = None) -> str:
    """List EC2 volumes.
Args:
    region: AWS region (default: eu-central-1)
    filters: Optional list of filter dictionaries. 
             Example: [{"Name": "status", "Values": ["available"]}]
    """
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
    """Delete an EC2 volume. Use with caution!
    Args:
        volume_id: ID of the volume to delete
        region: AWS region (default: eu-central-1)
    """
    try:
        ec2 = boto3.client('ec2', region_name=region)
        ec2.delete_volume(VolumeId=volume_id)
        return f"✅ Volume {volume_id} has been successfully deleted in {region}."
    except ClientError as e:
        return f"❌ Error deleting volume in {region}: {e}"


@tool
def list_snapshots(region: str = region_default, filters: list = None) -> str:
    """List EC2 snapshots.
Args:
    region: AWS region (default: eu-central-1)
    filters: Optional list of filter dictionaries. 
             Example: [{"Name": "status", "Values": ["available"]}]
    """
    try:
        ec2 = boto3.client('ec2', region_name=region)
        
        params = {"OwnerIds": ["self"]}   #
        
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
    """Delete an EC2 snapshot. Use with caution!
    Args:
        snapshot_id: ID of the snapshot to delete
        region: AWS region (default: eu-central-1)
    """
    try:
        ec2 = boto3.client('ec2', region_name=region)
        ec2.delete_snapshot(SnapshotId=snapshot_id)
        return f"✅ Snapshot {snapshot_id} has been successfully deleted in {region}."
    except ClientError as e:
        return f"❌ Error deleting snapshot in {region}: {e}"
    
@tool
def find_old_resources(region: str = region_default, min_age_days: int = 30) -> str:
    """Find EC2 volumes and snapshots older than a given number of days.
Args:
    region: AWS region (default: eu-central-1)
    min_age_days: minimum age in days to be flagged as old (default: 30)
    """
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
    model_id="eu.anthropic.claude-sonnet-4-6"
)

agent = Agent(
    model=model,
    tools=[list_volumes, delete_volume, list_snapshots, delete_snapshot, find_old_resources],
    system_prompt="""
    
You are helpful AWS assistant with 10 years experience as AWS Senior Cloud Engineer in Fortune500 companies. 

You can work in any AWS region. The user can specify region like "eu-central-1", "eu-west-1", "us-east-1", etc.

DO NOT take ANY actions in Amazon AWS except following on the list:

1) list volumes
2) delete volumes but only those with following parameters:
    -   volume state = available
    -   not attached to any resources
3) list snapshots
4) delete snapshots
5) find EC2 volumes and snapshots older than (default: 30 days)
6) create report, table in markdown, with info about volumes OR/AND snapshots from all regions

Do not answer on any other questions except related to actual actions mentioned above.

Answer in short, technical, merit-based, but satisfying way. Be a bit like Cookie Monster in AWS. Let's make a tool funny.

Always confirm delete operation with YES/NO. Confirm deletion two times before execution - inform the user beforehand."""
)

if __name__ == "__main__":
    print() 
    print("🚀 Agent ready - volumes and snapshots management.")
    print("Available commands: list volumes, delete volumes, list snapshots, delete snapshots, find old resources, create ebs report.")
    print()
    print("Say hello to start.")
    print("If you want to exit, type: exit or quit")

# Color codes
    GREEN = "\033[92m"
    RESET = "\033[0m"

    while True:
        user_input = input(f"\n{GREEN}You:{RESET} ")
        #user_input = input("\nYou: ")
        print()
        if user_input.lower() in ["exit", "quit"]:
            print("\nGoodbye! 👋")
            break
        response = agent(user_input)
        print()                                   # empty line
        #print(f"\nAgent: {response}")
