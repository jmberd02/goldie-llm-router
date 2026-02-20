import os
import boto3

# Load env vars from .env file
with open('llm-router/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key] = value.strip('"').strip("'")

client = boto3.client(
    'bedrock',
    region_name=os.getenv('AWS_REGION', 'us-east-1'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    aws_session_token=os.getenv('AWS_SESSION_TOKEN')
)

response = client.list_foundation_models()
print("Available Anthropic models:\n")
for model in response['modelSummaries']:
    if 'anthropic' in model['modelId'].lower():
        print(f"  {model['modelId']}")