"""Slack message templates for different insight types."""

from typing import Dict, List, Any, Optional
from datetime import datetime
from jinja2 import Environment, BaseLoader, Template
import json

from ..models.notification import Insight, InsightType, Priority


class SlackMessageTemplates:
    """Manages Slack message templates for different insight types."""
    
    def __init__(self):
        self.env = Environment(loader=BaseLoader())
        self._register_filters()
    
    def _register_filters(self):
        """Register custom Jinja2 filters."""
        self.env.filters['currency'] = lambda x: f"${x:,.2f}" if x else "N/A"
        self.env.filters['millions'] = lambda x: f"${x/1e6:.1f}M" if x and x >= 1e6 else f"${x:,.0f}" if x else "N/A"
        self.env.filters['date'] = lambda x: x.strftime("%B %d, %Y") if x else "N/A"
        self.env.filters['truncate'] = lambda x, n=100: x[:n] + "..." if x and len(x) > n else x
    
    def get_base_blocks(self, insight: Insight) -> List[Dict[str, Any]]:
        """Get base message blocks common to all insight types."""
        blocks = []
        
        # Header with priority indicator
        priority_emoji = {
            Priority.LOW: "🟢",
            Priority.NORMAL: "🔵",
            Priority.HIGH: "🟠",
            Priority.CRITICAL: "🔴"
        }.get(insight.priority, "⚪")
        
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{priority_emoji} {insight.title}",
                "emoji": True
            }
        })
        
        # Company context
        company_text = f"*{insight.company.name}*"
        if insight.company.ticker:
            company_text += f" ({insight.company.ticker})"
        if insight.company.sector:
            company_text += f" • {insight.company.sector}"
        
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": company_text
                }
            ]
        })
        
        # Summary
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": insight.summary
            }
        })
        
        return blocks
    
    def get_regulatory_approval_blocks(self, insight: Insight) -> List[Dict[str, Any]]:
        """Generate blocks for regulatory approval notifications."""
        blocks = self.get_base_blocks(insight)
        data = insight.data
        
        # Approval details
        details = []
        if data.regulatory_body:
            details.append(f"*Regulatory Body:* {data.regulatory_body}")
        if data.drug_name:
            details.append(f"*Drug:* {data.drug_name}")
        if data.indication:
            details.append(f"*Indication:* {data.indication}")
        if data.approval_type:
            details.append(f"*Approval Type:* {data.approval_type}")
        
        if details:
            blocks.append({
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": detail}
                    for detail in details[:4]  # Max 4 fields
                ]
            })
        
        # Add divider before actions
        blocks.append({"type": "divider"})
        
        return blocks
    
    def get_clinical_trial_blocks(self, insight: Insight) -> List[Dict[str, Any]]:
        """Generate blocks for clinical trial updates."""
        blocks = self.get_base_blocks(insight)
        data = insight.data
        
        # Trial details
        details = []
        if data.trial_phase:
            details.append(f"*Phase:* {data.trial_phase}")
        if data.trial_status:
            details.append(f"*Status:* {data.trial_status}")
        if data.patient_count:
            details.append(f"*Patients:* {data.patient_count:,}")
        if data.primary_endpoint:
            details.append(f"*Primary Endpoint:* {data.primary_endpoint}")
        
        if details:
            blocks.append({
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": detail}
                    for detail in details[:4]
                ]
            })
        
        blocks.append({"type": "divider"})
        return blocks
    
    def get_merger_acquisition_blocks(self, insight: Insight) -> List[Dict[str, Any]]:
        """Generate blocks for M&A announcements."""
        blocks = self.get_base_blocks(insight)
        data = insight.data
        
        # Deal details
        details = []
        if data.acquirer:
            details.append(f"*Acquirer:* {data.acquirer}")
        if data.target:
            details.append(f"*Target:* {data.target}")
        if data.deal_value:
            details.append(f"*Deal Value:* {self.env.filters['millions'](data.deal_value)}")
        if data.deal_type:
            details.append(f"*Type:* {data.deal_type.title()}")
        
        if details:
            blocks.append({
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": detail}
                    for detail in details[:4]
                ]
            })
        
        blocks.append({"type": "divider"})
        return blocks
    
    def get_funding_round_blocks(self, insight: Insight) -> List[Dict[str, Any]]:
        """Generate blocks for funding round announcements."""
        blocks = self.get_base_blocks(insight)
        data = insight.data
        
        # Funding details
        details = []
        if data.funding_amount:
            details.append(f"*Amount:* {self.env.filters['millions'](data.funding_amount)}")
        if data.funding_round:
            details.append(f"*Round:* {data.funding_round}")
        if data.lead_investor:
            details.append(f"*Lead Investor:* {data.lead_investor}")
        if data.valuation:
            details.append(f"*Valuation:* {self.env.filters['millions'](data.valuation)}")
        
        if details:
            blocks.append({
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": detail}
                    for detail in details[:4]
                ]
            })
        
        blocks.append({"type": "divider"})
        return blocks
    
    def get_partnership_blocks(self, insight: Insight) -> List[Dict[str, Any]]:
        """Generate blocks for partnership announcements."""
        blocks = self.get_base_blocks(insight)
        data = insight.data
        
        # Partnership details
        if data.partner_companies:
            partners_text = "*Partners:* " + ", ".join(data.partner_companies[:3])
            if len(data.partner_companies) > 3:
                partners_text += f" +{len(data.partner_companies) - 3} more"
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": partners_text
                }
            })
        
        details = []
        if data.partnership_type:
            details.append(f"*Type:* {data.partnership_type}")
        if data.deal_terms:
            details.append(f"*Terms:* {self.env.filters['truncate'](data.deal_terms, 50)}")
        
        if details:
            blocks.append({
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": detail}
                    for detail in details
                ]
            })
        
        blocks.append({"type": "divider"})
        return blocks
    
    def get_custom_blocks(self, insight: Insight) -> List[Dict[str, Any]]:
        """Generate blocks for custom alerts."""
        blocks = self.get_base_blocks(insight)
        
        # Add any extra data as fields
        if insight.data.extra_data:
            fields = []
            for key, value in list(insight.data.extra_data.items())[:4]:
                fields.append({
                    "type": "mrkdwn",
                    "text": f"*{key.replace('_', ' ').title()}:* {value}"
                })
            
            if fields:
                blocks.append({
                    "type": "section",
                    "fields": fields
                })
        
        blocks.append({"type": "divider"})
        return blocks
    
    def add_action_buttons(self, blocks: List[Dict[str, Any]], insight_id: str) -> List[Dict[str, Any]]:
        """Add interactive action buttons to the message."""
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ Mark as Reviewed",
                        "emoji": True
                    },
                    "style": "primary",
                    "action_id": "mark_reviewed",
                    "value": insight_id
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📊 View Details",
                        "emoji": True
                    },
                    "action_id": "view_details",
                    "value": insight_id
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🔗 Source",
                        "emoji": True
                    },
                    "url": insight.source_url if insight.source_url else "#",
                    "action_id": "view_source",
                    "value": insight_id
                }
            ]
        })
        
        return blocks
    
    def add_metadata_context(self, blocks: List[Dict[str, Any]], insight: Insight) -> List[Dict[str, Any]]:
        """Add metadata context to the message."""
        context_elements = []
        
        # Confidence score
        if insight.confidence_score is not None:
            confidence_pct = int(insight.confidence_score * 100)
            confidence_emoji = "🟢" if confidence_pct >= 80 else "🟡" if confidence_pct >= 60 else "🔴"
            context_elements.append({
                "type": "mrkdwn",
                "text": f"{confidence_emoji} Confidence: {confidence_pct}%"
            })
        
        # Tags
        if insight.tags:
            tags_text = " ".join([f"`{tag}`" for tag in insight.tags[:5]])
            context_elements.append({
                "type": "mrkdwn",
                "text": f"Tags: {tags_text}"
            })
        
        # Timestamp
        context_elements.append({
            "type": "mrkdwn",
            "text": f"Generated: <!date^{int(insight.created_at.timestamp())}^{date_num} at {time}|{insight.created_at.isoformat()}>"
        })
        
        if context_elements:
            blocks.append({
                "type": "context",
                "elements": context_elements[:10]  # Max 10 elements
            })
        
        return blocks
    
    def generate_message(self, insight: Insight, include_actions: bool = True) -> Dict[str, Any]:
        """Generate a complete Slack message for an insight."""
        # Get type-specific blocks
        type_handlers = {
            InsightType.REGULATORY_APPROVAL: self.get_regulatory_approval_blocks,
            InsightType.CLINICAL_TRIAL: self.get_clinical_trial_blocks,
            InsightType.MERGER_ACQUISITION: self.get_merger_acquisition_blocks,
            InsightType.FUNDING_ROUND: self.get_funding_round_blocks,
            InsightType.PARTNERSHIP: self.get_partnership_blocks,
            InsightType.CUSTOM: self.get_custom_blocks,
        }
        
        handler = type_handlers.get(insight.type, self.get_custom_blocks)
        blocks = handler(insight)
        
        # Add actions if requested
        if include_actions:
            blocks = self.add_action_buttons(blocks, insight.id)
        
        # Add metadata
        blocks = self.add_metadata_context(blocks, insight)
        
        # Create the message
        message = {
            "blocks": blocks,
            "text": f"{insight.title} - {insight.summary[:150]}..."  # Fallback text
        }
        
        # Add thread broadcast for high priority
        if insight.priority in [Priority.HIGH, Priority.CRITICAL]:
            message["reply_broadcast"] = True
        
        return message
    
    def generate_thread_reply(self, insight: Insight) -> Dict[str, Any]:
        """Generate a detailed thread reply with full analysis."""
        blocks = []
        
        # Header
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "📋 Detailed Analysis",
                "emoji": True
            }
        })
        
        # Full analysis
        if insight.detailed_analysis:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": insight.detailed_analysis[:3000]  # Slack limit
                }
            })
        
        # Related companies
        if insight.related_companies:
            related_text = "*Related Companies:*\n"
            for company in insight.related_companies[:5]:
                related_text += f"• {company.name}"
                if company.ticker:
                    related_text += f" ({company.ticker})"
                related_text += "\n"
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": related_text
                }
            })
        
        return {"blocks": blocks}
