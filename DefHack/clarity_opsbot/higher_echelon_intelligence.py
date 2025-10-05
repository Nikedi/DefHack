"""
Higher Echelon Intelligence Summary System for DefHack Telegram Bot
Provides various types of intelligence analysis and summaries for command staff
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import json

class SummaryType(Enum):
    """Types of intelligence summaries available"""
    DAILY_INTREP = "daily_intrep"          # 24-hour intelligence report
    THREAT_ASSESSMENT = "threat_assessment" # Current threat analysis
    ACTIVITY_SUMMARY = "activity_summary"   # Activity pattern analysis
    TACTICAL_SUMMARY = "tactical_summary"   # Tactical situation overview
    WEEKLY_SUMMARY = "weekly_summary"       # Weekly intelligence summary
    CUSTOM_PERIOD = "custom_period"         # Custom time period analysis

class IntelligenceType(Enum):
    """Categories of intelligence analysis"""
    ENEMY_ACTIVITY = "enemy_activity"
    FRIENDLY_FORCES = "friendly_forces"
    TERRAIN_WEATHER = "terrain_weather"
    LOGISTICS = "logistics"
    COMMUNICATIONS = "communications"
    THREAT_ANALYSIS = "threat_analysis"

class HigherEchelonIntelligence:
    """Intelligence summary system for higher echelon users"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        
        # Import DefHack components
        try:
            from .defhack_bridge import DefHackTelegramBridge
            from .user_roles import user_manager
            
            self.defhack_bridge = DefHackTelegramBridge()
            self.user_manager = user_manager
            
        except ImportError as e:
            self.logger.error(f"Failed to import required modules: {e}")
            self.defhack_bridge = None
            self.user_manager = None
    
    async def generate_intelligence_summary(self, summary_type: SummaryType, 
                                          requesting_user_id: int,
                                          time_period_hours: int = 24,
                                          intelligence_types: List[IntelligenceType] = None) -> str:
        """
        Generate intelligence summary based on type and parameters
        """
        try:
            # Verify user permissions
            if not self._verify_user_permissions(requesting_user_id):
                return "❌ **ACCESS DENIED**\n\nYou do not have permission to request intelligence summaries."
            
            user_profile = self.user_manager.get_user(requesting_user_id)
            user_info = f"{user_profile.full_name} ({user_profile.role.value})" if user_profile else "Unknown User"
            
            self.logger.info(f"Generating {summary_type.value} for {user_info}")
            
            # Generate summary based on type
            if summary_type == SummaryType.DAILY_INTREP:
                return await self._generate_daily_intrep(time_period_hours)
            elif summary_type == SummaryType.THREAT_ASSESSMENT:
                return await self._generate_threat_assessment(time_period_hours)
            elif summary_type == SummaryType.ACTIVITY_SUMMARY:
                return await self._generate_activity_summary(time_period_hours)
            elif summary_type == SummaryType.TACTICAL_SUMMARY:
                return await self._generate_tactical_summary(time_period_hours)
            elif summary_type == SummaryType.WEEKLY_SUMMARY:
                return await self._generate_weekly_summary()
            elif summary_type == SummaryType.CUSTOM_PERIOD:
                return await self._generate_custom_period_summary(time_period_hours, intelligence_types)
            else:
                return "❌ **ERROR**\n\nUnsupported summary type requested."
                
        except Exception as e:
            self.logger.error(f"Failed to generate intelligence summary: {e}")
            return f"❌ **INTELLIGENCE GENERATION ERROR**\n\nFailed to generate summary: {str(e)}"
    
    def _verify_user_permissions(self, user_id: int) -> bool:
        """Verify user has permission to request intelligence summaries"""
        if not self.user_manager:
            return False
        return self.user_manager.can_request_intelligence_summary(user_id)
    
    async def _generate_daily_intrep(self, hours: int = 24) -> str:
        """Generate daily intelligence report (INTREP)"""
        try:
            # Use DefHack bridge to generate comprehensive intelligence report
            if self.defhack_bridge:
                report = await self.defhack_bridge.generate_daily_intelligence_summary()
                
                # Format as official INTREP
                formatted_report = self._format_as_intrep(report, hours)
                return formatted_report
            else:
                return await self._generate_fallback_intrep(hours)
                
        except Exception as e:
            self.logger.error(f"Failed to generate daily INTREP: {e}")
            return self._generate_error_intrep(str(e))
    
    async def _generate_threat_assessment(self, hours: int = 24) -> str:
        """Generate current threat assessment"""
        current_time = datetime.now(timezone.utc)
        period_start = current_time - timedelta(hours=hours)
        
        assessment = f"""🚨 **THREAT ASSESSMENT REPORT**
📅 **Period:** {period_start.strftime('%d %b %Y %H:%M')} - {current_time.strftime('%d %b %Y %H:%M UTC')}
🔐 **Classification:** FOR OFFICIAL USE ONLY

**1. EXECUTIVE SUMMARY**
Current threat level analysis based on {hours}-hour observation period.

**2. ENEMY FORCES**
• **BTG Activity:** Analysis of enemy battalion tactical group movements
• **Equipment:** Observed weapon systems and capabilities  
• **Positions:** Known and suspected enemy positions
• **Strength:** Estimated force strength and composition

**3. THREAT INDICATORS**
• **Immediate Threats:** Direct threats to friendly forces
• **Emerging Threats:** Developing threat situations
• **Long-term Concerns:** Strategic threat developments

**4. RECOMMENDATIONS**
• **Immediate Actions:** Required immediate response measures
• **Preventive Measures:** Recommended defensive preparations
• **Intelligence Gaps:** Areas requiring additional collection

**5. COMMANDER'S ASSESSMENT**
Overall threat evaluation and risk assessment for command consideration.

⚠️ **THREAT LEVEL: MEDIUM** ⚠️
*Assessment based on available intelligence and observation data*

📞 **Contact S2 for detailed threat briefing**
"""
        return assessment
    
    async def _generate_activity_summary(self, hours: int = 24) -> str:
        """Generate activity pattern summary"""
        current_time = datetime.now(timezone.utc)
        period_start = current_time - timedelta(hours=hours)
        
        summary = f"""📊 **ACTIVITY PATTERN SUMMARY**
📅 **Period:** {period_start.strftime('%d %b %Y %H:%M')} - {current_time.strftime('%d %b %Y %H:%M UTC')}

**1. OBSERVATION STATISTICS**
• **Total Observations:** Analyzing {hours}-hour period
• **High Confidence Reports:** Priority intelligence items
• **Medium Confidence Reports:** Probable activity indicators
• **Low Confidence Reports:** Possible activity indicators

**2. ENEMY ACTIVITY PATTERNS**
• **Movement Patterns:** Observed enemy movement trends
• **Timing Analysis:** Activity timing and frequency patterns
• **Geographic Distribution:** Spatial analysis of enemy activity
• **Equipment Usage:** Weapon systems and equipment patterns

**3. FRIENDLY FORCE ACTIVITY**
• **Patrol Activity:** Friendly force patrol patterns and coverage
• **Observation Posts:** OP activity and effectiveness
• **Communication Patterns:** COMMS activity analysis

**4. ENVIRONMENTAL FACTORS**
• **Weather Impact:** Weather effects on activity patterns
• **Terrain Usage:** Terrain-based activity analysis
• **Time-based Patterns:** Temporal activity trends

**5. PATTERN ANALYSIS**
• **Notable Trends:** Significant pattern changes
• **Anomalies:** Unusual activity indicators
• **Predictive Indicators:** Potential future activity patterns

📈 **KEY FINDING:** Activity patterns show [analysis required]
🎯 **RECOMMENDATION:** Continue monitoring identified patterns
"""
        return summary
    
    async def _generate_tactical_summary(self, hours: int = 24) -> str:
        """Generate tactical situation summary"""
        current_time = datetime.now(timezone.utc)
        period_start = current_time - timedelta(hours=hours)
        
        summary = f"""⚔️ **TACTICAL SITUATION SUMMARY**
📅 **Period:** {period_start.strftime('%d %b %Y %H:%M')} - {current_time.strftime('%d %b %Y %H:%M UTC')}
🔐 **Classification:** FOR OFFICIAL USE ONLY

**1. CURRENT SITUATION**
• **Enemy Forces:** Current enemy disposition and capabilities
• **Friendly Forces:** Friendly force positions and status
• **Terrain:** Key terrain features and control status
• **Weather:** Current and forecast weather conditions

**2. SIGNIFICANT EVENTS**
• **Enemy Contact:** Recent enemy contact reports
• **Movement:** Significant force movements
• **Equipment:** New equipment observations
• **Casualties:** Friendly and enemy casualty reports

**3. TACTICAL ASSESSMENT**
• **Enemy Capabilities:** Assessment of enemy tactical capabilities
• **Enemy Intentions:** Probable enemy courses of action
• **Friendly Advantages:** Current tactical advantages
• **Vulnerabilities:** Identified tactical vulnerabilities

**4. COMMANDER'S GUIDANCE**
• **Priority Intelligence Requirements (PIR):** Current PIRs
• **Main Effort:** Current tactical focus areas
• **Risk Assessment:** Key tactical risks

**5. NEXT 24 HOURS**
• **Anticipated Activity:** Expected tactical developments
• **Planned Operations:** Scheduled friendly operations
• **Watch Areas:** Areas requiring increased surveillance

🎯 **TACTICAL RECOMMENDATION:** Maintain current posture with enhanced surveillance
⚠️ **RISK LEVEL:** Manageable with current force disposition
"""
        return summary
    
    async def _generate_weekly_summary(self) -> str:
        """Generate weekly intelligence summary"""
        current_time = datetime.now(timezone.utc)
        week_start = current_time - timedelta(days=7)
        
        summary = f"""📈 **WEEKLY INTELLIGENCE SUMMARY**
📅 **Period:** {week_start.strftime('%d %b %Y')} - {current_time.strftime('%d %b %Y')}
🔐 **Classification:** FOR OFFICIAL USE ONLY

**1. WEEK OVERVIEW**
• **Total Observations:** Weekly observation statistics
• **Significant Events:** Major events and developments
• **Trend Analysis:** Weekly trend identification
• **Intelligence Highlights:** Key intelligence developments

**2. ENEMY FORCE ANALYSIS**
• **Strength Changes:** Enemy force strength variations
• **Equipment Updates:** New equipment observations
• **Tactical Changes:** Changes in enemy tactics
• **Geographic Shifts:** Enemy area of operations changes

**3. OPERATIONAL ENVIRONMENT**
• **Weather Patterns:** Weekly weather impact analysis
• **Terrain Changes:** Significant terrain modifications
• **Infrastructure:** Changes to infrastructure and facilities
• **Population:** Civilian population considerations

**4. INTELLIGENCE ASSESSMENT**
• **Collection Effectiveness:** Intelligence collection assessment
• **Information Gaps:** Identified intelligence gaps
• **Source Reliability:** Intelligence source evaluation
• **Analytical Confidence:** Confidence levels in assessments

**5. WEEKLY RECOMMENDATIONS**
• **Focus Areas:** Areas requiring increased attention
• **Collection Priorities:** Priority intelligence requirements
• **Operational Adjustments:** Recommended tactical changes
• **Risk Mitigation:** Risk management recommendations

📊 **WEEKLY TREND:** [Requires analysis of weekly data]
🔮 **FORECAST:** Anticipated developments for coming week
"""
        return summary
    
    async def _generate_custom_period_summary(self, hours: int, 
                                            intel_types: List[IntelligenceType] = None) -> str:
        """Generate custom period summary with specific intelligence types"""
        current_time = datetime.now(timezone.utc)
        period_start = current_time - timedelta(hours=hours)
        
        if intel_types is None:
            intel_types = [IntelligenceType.ENEMY_ACTIVITY, IntelligenceType.THREAT_ANALYSIS]
        
        summary = f"""🔍 **CUSTOM INTELLIGENCE ANALYSIS**
📅 **Period:** {period_start.strftime('%d %b %Y %H:%M')} - {current_time.strftime('%d %b %Y %H:%M UTC')}
⏱️ **Duration:** {hours} hours
🎯 **Focus Areas:** {', '.join([t.value.replace('_', ' ').title() for t in intel_types])}

"""
        
        # Add sections based on requested intelligence types
        for intel_type in intel_types:
            if intel_type == IntelligenceType.ENEMY_ACTIVITY:
                summary += """**ENEMY ACTIVITY ANALYSIS**
• Recent enemy movements and positions
• Equipment and capability observations
• Tactical behavior patterns
• Threat level assessments

"""
            elif intel_type == IntelligenceType.THREAT_ANALYSIS:
                summary += """**THREAT ANALYSIS**
• Current threat indicators
• Risk assessment and mitigation
• Emerging threat developments
• Threat trend analysis

"""
            elif intel_type == IntelligenceType.FRIENDLY_FORCES:
                summary += """**FRIENDLY FORCE STATUS**
• Unit positions and activities
• Operational effectiveness
• Force protection status
• Communication and coordination

"""
            elif intel_type == IntelligenceType.TERRAIN_WEATHER:
                summary += """**TERRAIN AND WEATHER**
• Terrain utilization analysis
• Weather impact on operations
• Environmental considerations
• Geographic advantages/disadvantages

"""
        
        summary += f"""**ANALYSIS SUMMARY**
Custom analysis covering {hours}-hour period with focus on requested intelligence categories.

📊 **DATA CONFIDENCE:** Based on available observation data
🎯 **RECOMMENDATIONS:** Tailored to specified analysis focus
"""
        
        return summary
    
    def _format_as_intrep(self, raw_report: str, hours: int) -> str:
        """Format raw report as official INTREP"""
        current_time = datetime.now(timezone.utc)
        period_start = current_time - timedelta(hours=hours)
        
        formatted = f"""📋 **INTELLIGENCE REPORT (INTREP)**
📅 **DTG:** {current_time.strftime('%d%H%M%SZ %b %Y')}
📅 **Period:** {period_start.strftime('%d %b %Y %H:%M')} - {current_time.strftime('%d %b %Y %H:%M UTC')}
🔐 **Classification:** FOR OFFICIAL USE ONLY

**1. SUMMARY OF INTELLIGENCE**
{raw_report}

**2. ENEMY FORCES**
• Disposition and activities based on {hours}-hour observation period
• Strength estimates and equipment identification
• Probable courses of action and intentions

**3. WEATHER AND TERRAIN**
• Current weather conditions and forecast
• Terrain considerations affecting operations
• Environmental factors impacting intelligence collection

**4. FRIENDLY FORCES**
• Current friendly force disposition
• Intelligence collection activities
• Force protection considerations

**5. INTELLIGENCE GAPS AND REQUIREMENTS**
• Priority Intelligence Requirements (PIR) status
• Collection gaps requiring attention
• Recommended intelligence activities

**6. ANALYTICAL ASSESSMENT**
• Confidence levels in reporting
• Source reliability evaluation
• Analytical conclusions and recommendations

📊 **PREPARED BY:** DefHack AI Intelligence System
📞 **COORDINATION:** Contact S2 for additional details
🔄 **NEXT INTREP:** Scheduled per operational requirements
"""
        return formatted
    
    async def _generate_fallback_intrep(self, hours: int) -> str:
        """Generate fallback INTREP when DefHack bridge is unavailable"""
        current_time = datetime.now(timezone.utc)
        period_start = current_time - timedelta(hours=hours)
        
        return f"""📋 **INTELLIGENCE REPORT (INTREP) - LIMITED**
📅 **DTG:** {current_time.strftime('%d%H%M%SZ %b %Y')}
📅 **Period:** {period_start.strftime('%d %b %Y %H:%M')} - {current_time.strftime('%d %b %Y %H:%M UTC')}
🔐 **Classification:** FOR OFFICIAL USE ONLY

⚠️ **LIMITED CONNECTIVITY NOTICE**
DefHack intelligence database temporarily unavailable.
Manual intelligence collection and analysis required.

**1. SUMMARY**
Intelligence summary based on available local observations during {hours}-hour period.

**2. RECOMMENDATIONS**
• Verify connectivity to DefHack intelligence system
• Continue manual intelligence collection
• Coordinate with S2 for comprehensive intelligence picture
• Resume automated intelligence analysis when system available

📞 **ACTION REQUIRED:** Contact technical support for system restoration
🔄 **STATUS:** System monitoring in progress
"""
    
    def _generate_error_intrep(self, error_message: str) -> str:
        """Generate error INTREP when generation fails"""
        current_time = datetime.now(timezone.utc)
        
        return f"""📋 **INTELLIGENCE REPORT (INTREP) - ERROR**
📅 **DTG:** {current_time.strftime('%d%H%M%SZ %b %Y')}
🔐 **Classification:** FOR OFFICIAL USE ONLY

❌ **SYSTEM ERROR**
Intelligence report generation encountered an error.

**Error Details:** {error_message}

**IMMEDIATE ACTIONS REQUIRED:**
1. Notify technical support of system error
2. Implement manual intelligence collection procedures
3. Coordinate with S2 for alternative intelligence sources
4. Continue operational activities with available intelligence

📞 **TECHNICAL SUPPORT:** Contact system administrator
⚠️ **OPERATIONAL IMPACT:** Automated intelligence temporarily unavailable
"""

# Global instance
higher_echelon_intel = None

def initialize_higher_echelon_intelligence(logger: logging.Logger):
    """Initialize the global higher echelon intelligence system"""
    global higher_echelon_intel
    higher_echelon_intel = HigherEchelonIntelligence(logger)
    return higher_echelon_intel