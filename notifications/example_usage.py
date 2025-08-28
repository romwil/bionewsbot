#!/usr/bin/env python3
"""
Example script demonstrating how to use the BioNewsBot notification service.
"""

import asyncio
import json
from datetime import datetime
import httpx
from typing import Dict, Any


# Configuration
NOTIFICATION_SERVICE_URL = "http://localhost:8001"
WEBHOOK_SECRET = "your-webhook-secret-here"  # Must match service config


async def send_regulatory_approval():
    """Send a regulatory approval notification."""
    insight = {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "type": "regulatory_approval",
        "priority": "high",
        "title": "FDA Approves Keytruda for Advanced Melanoma",
        "summary": "The FDA has granted accelerated approval for Keytruda (pembrolizumab) for the treatment of advanced melanoma patients who have progressed on prior therapies.",
        "company": {
            "name": "Merck & Co.",
            "ticker": "MRK",
            "sector": "Pharmaceuticals"
        },
        "metadata": {
            "regulatory_body": "FDA",
            "drug_name": "Keytruda (pembrolizumab)",
            "indication": "Advanced Melanoma",
            "approval_type": "Accelerated Approval",
            "approval_date": datetime.utcnow().isoformat()
        },
        "source_url": "https://www.fda.gov/news-events/press-announcements/example",
        "created_at": datetime.utcnow().isoformat()
    }
    
    payload = {
        "insight": insight,
        "channels": ["#alerts"]  # Optional: specify channels
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NOTIFICATION_SERVICE_URL}/webhooks/insights",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": "sha256=example"  # In production, calculate HMAC
            }
        )
        
        print(f"Regulatory Approval: {response.status_code}")
        print(json.dumps(response.json(), indent=2))


async def send_clinical_trial_update():
    """Send a clinical trial update notification."""
    insight = {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "type": "clinical_trial",
        "priority": "normal",
        "title": "Phase 3 Trial Shows Positive Results",
        "summary": "BioNTech announces positive topline results from Phase 3 trial of BNT162b2, meeting primary efficacy endpoint with 95% efficacy in preventing COVID-19.",
        "company": {
            "name": "BioNTech SE",
            "ticker": "BNTX",
            "sector": "Biotechnology"
        },
        "metadata": {
            "trial_phase": "Phase 3",
            "trial_status": "Completed",
            "patient_count": "43,548",
            "primary_endpoint": "Prevention of COVID-19",
            "efficacy": "95%",
            "completion_date": datetime.utcnow().isoformat()
        },
        "source_url": "https://clinicaltrials.gov/example",
        "created_at": datetime.utcnow().isoformat()
    }
    
    payload = {
        "insight": insight
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NOTIFICATION_SERVICE_URL}/webhooks/insights",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": "sha256=example"
            }
        )
        
        print(f"\nClinical Trial: {response.status_code}")
        print(json.dumps(response.json(), indent=2))


async def send_ma_announcement():
    """Send an M&A announcement notification."""
    insight = {
        "id": "550e8400-e29b-41d4-a716-446655440003",
        "type": "ma_announcement",
        "priority": "high",
        "title": "Pfizer to Acquire Seagen for $43 Billion",
        "summary": "Pfizer announces definitive agreement to acquire Seagen for $229 per share in cash, strengthening its oncology portfolio with four approved cancer medicines.",
        "company": {
            "name": "Pfizer Inc.",
            "ticker": "PFE",
            "sector": "Pharmaceuticals"
        },
        "metadata": {
            "acquirer": "Pfizer Inc.",
            "target": "Seagen Inc.",
            "deal_value": "$43 billion",
            "price_per_share": "$229",
            "premium": "32.7%",
            "expected_close": "Q4 2023",
            "announcement_date": datetime.utcnow().isoformat()
        },
        "source_url": "https://www.pfizer.com/news/press-release/example",
        "created_at": datetime.utcnow().isoformat()
    }
    
    payload = {
        "insight": insight
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NOTIFICATION_SERVICE_URL}/webhooks/insights",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": "sha256=example"
            }
        )
        
        print(f"\nM&A Announcement: {response.status_code}")
        print(json.dumps(response.json(), indent=2))


async def check_service_health():
    """Check the health of the notification service."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{NOTIFICATION_SERVICE_URL}/webhooks/health")
        
        print("\nService Health:")
        print(json.dumps(response.json(), indent=2))


async def get_service_status():
    """Get the status of the notification service."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{NOTIFICATION_SERVICE_URL}/status")
        
        print("\nService Status:")
        print(json.dumps(response.json(), indent=2))


async def main():
    """Run example notifications."""
    print("BioNewsBot Notification Service Example")
    print("=" * 40)
    
    # Check service health
    await check_service_health()
    
    # Get service status
    await get_service_status()
    
    # Send example notifications
    print("\nSending example notifications...\n")
    
    await send_regulatory_approval()
    await asyncio.sleep(1)  # Small delay between notifications
    
    await send_clinical_trial_update()
    await asyncio.sleep(1)
    
    await send_ma_announcement()
    
    print("\nExample notifications sent!")
    print("Check your Slack channels for the notifications.")


if __name__ == "__main__":
    asyncio.run(main())
