import os
import boto3
import json
import base64
from app.api.schemas import BlueprintVerificationResult
import instructor

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

def get_bedrock_client():
    return boto3.client(
        service_name="bedrock-runtime",
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )

def analyze_blueprint_image(image_bytes: bytes, prompt: str, media_type: str = "image/jpeg") -> BlueprintVerificationResult:
    """
    Sends an image to Claude 3.5 Sonnet on Amazon Bedrock to extract structured JSON.
    """
    client = instructor.from_litellm(get_bedrock_client())
    
    # Base64 encode the image
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')

    response = client.chat.completions.create(
        model="bedrock/meta.llama4-maverick-17b-instruct-v1:0",
        max_tokens=2048,
        response_model=BlueprintVerificationResult,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": f"You are an expert structural engineer and architect analyzing blueprints. {prompt}"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{image_base64}"
                        }
                    }
                ]
            }
        ]
    )
    return response

def analyze_blueprint_pdf(pdf_bytes: bytes, prompt: str) -> BlueprintVerificationResult:
    """
    Sends a PDF to Claude 3.5 Sonnet on Amazon Bedrock.
    """
    # Note: Llama Vision doesn't currently easily parse multi-page PDFs out of the box through LiteLLM/OpenAI standard wrappers.
    # Usually you would convert the PDF to an image first, but we can pass it as a document if LiteLLM proxy handles it.
    client = instructor.from_litellm(get_bedrock_client())
    
    # Base64 encode the pdf
    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

    response = client.chat.completions.create(
        model="bedrock/meta.llama4-maverick-17b-instruct-v1:0",
        max_tokens=2048,
        response_model=BlueprintVerificationResult,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": f"You are an expert structural engineer and architect analyzing blueprints. {prompt}"
                    },
                    {
                        "type": "image_url", # Need to treat it loosely as an image URL for litellm standard Vision if PDF isn't strictly supported
                        "image_url": {
                            "url": f"data:application/pdf;base64,{pdf_base64}"
                        }
                    }
                ]
            }
        ]
    )
    return response

