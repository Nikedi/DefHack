#!/usr/bin/env python3
"""
Military Prompt Templates for DefHack LLM Functions
Professional military prompt engineering for tactical operations
"""

class MilitaryPromptTemplates:
    """Collection of military prompt templates for different operational needs"""
    
    @staticmethod
    def frago_template(observation: dict) -> str:
        """FRAGO (Fragmentary Order) prompt template"""
        target = observation.get('what', 'Unknown Target')
        location = observation.get('mgrs', 'Unknown Location')
        amount = observation.get('amount', 1)
        confidence = observation.get('confidence', 0)
        time_str = observation.get('time_formatted', 'Unknown Time')
        observer = observation.get('observer_signature', 'Unknown')
        unit = observation.get('unit', 'Unknown Unit')
        
        threat_level = "HIGH" if confidence >= 90 else "MEDIUM" if confidence >= 80 else "LOW"
        
        return f"""
TASK: Generate a FRAGO (Fragmentary Order) for immediate tactical response.

OBSERVATION DATA:
- DTG: {time_str}
- TARGET: {target} (QTY: {amount})
- LOCATION: {location} (MGRS)
- CONFIDENCE: {confidence}% ({threat_level} PRIORITY)
- OBSERVER: {observer} ({unit})

FRAGO FORMAT REQUIREMENTS:
1. HEADER: FRAGO [Number] to OPORD [Reference]
2. SITUATION: Enemy situation based on observation
3. MISSION: Clear, concise mission statement
4. EXECUTION:
   a. Concept of Operations
   b. Tasks to Subordinate Units
   c. Coordinating Instructions
5. ADMIN/LOGISTICS: Supply, medical, transportation
6. COMMAND/SIGNAL: Command relationships and communications

TACTICAL CONSIDERATIONS:
- Apply doctrinal knowledge about {target} capabilities and vulnerabilities
- Consider immediate response timeline (0-4 hours)
- Include force protection measures appropriate to threat level
- Specify reconnaissance, surveillance, and engagement procedures
- Address coordination with adjacent units and higher headquarters

OUTPUT: Complete FRAGO in proper military format, ready for immediate dissemination.
"""

    @staticmethod
    def telegram_alert_template(observation: dict) -> str:
        """Telegram alert message prompt template"""
        target = observation.get('what', 'Unknown')
        location = observation.get('mgrs', 'Unknown')
        amount = observation.get('amount', 1)
        confidence = observation.get('confidence', 0)
        time_str = observation.get('time_formatted', 'Unknown')
        observer = observation.get('observer_signature', 'Observer')
        
        urgency_emoji = "🚨" if confidence >= 90 else "⚠️" if confidence >= 80 else "ℹ️"
        
        return f"""
TASK: Create concise Telegram alert message for tactical notification.

OBSERVATION:
- TIME: {time_str}
- TARGET: {target} (x{amount})
- LOCATION: {location}
- CONFIDENCE: {confidence}%
- OBSERVER: {observer}

MESSAGE REQUIREMENTS:
1. Maximum 200 characters for mobile readability
2. Lead with appropriate urgency emoji: {urgency_emoji}
3. Use military time format (HHMM Z)
4. Include essential tactical information: WHO, WHAT, WHERE, WHEN
5. End with confidence level and observer callsign
6. Professional tone suitable for command notifications

TACTICAL ABBREVIATIONS (use as appropriate):
- TK = Tank
- IFV = Infantry Fighting Vehicle  
- BTR = Armored Personnel Carrier
- RECCE = Reconnaissance
- INF = Infantry
- ARTY = Artillery

OUTPUT: Single, concise Telegram message ready for immediate transmission.
"""

    @staticmethod
    def intelligence_summary_template() -> str:
        """24-hour intelligence summary prompt template"""
        return """
TASK: Generate comprehensive 24-hour intelligence summary for command briefing.

INTELLIGENCE SUMMARY FORMAT:
1. EXECUTIVE SUMMARY
   - Key findings and immediate threats (2-3 sentences)
   - Overall threat assessment and priority concerns

2. TACTICAL SITUATION ANALYSIS
   - Enemy force composition observed
   - Geographic disposition and positioning
   - Activity patterns and operational tempo

3. THREAT ASSESSMENT BY CATEGORY
   - ARMOR: Tank and mechanized threats
   - INFANTRY: Dismounted and motorized elements  
   - ARTILLERY: Indirect fire capabilities
   - RECONNAISSANCE: Enemy surveillance activities
   - LOGISTICS: Supply and sustainment observations

4. PATTERN ANALYSIS
   - Temporal patterns (time-based activity)
   - Spatial patterns (geographic clustering)
   - Tactical patterns (operational signatures)

5. DOCTRINAL ANALYSIS
   - Apply BTG tactical doctrine from available documents
   - Compare observed activity to known enemy TTPs
   - Assess adherence to or deviation from doctrine

6. INTELLIGENCE GAPS
   - Missing critical information
   - Areas requiring additional collection
   - Priority intelligence requirements (PIRs)

7. RECOMMENDATIONS
   - Immediate action recommendations
   - Collection guidance for next 24 hours
   - Force protection measures

ANALYSIS STANDARDS:
- Use proper military intelligence terminology
- Cite document sources when applying doctrinal knowledge
- Include confidence assessments for all conclusions
- Reference specific MGRS coordinates and times
- Maintain professional intelligence community standards

OUTPUT: Complete intelligence summary suitable for command briefing and decision-making.
"""

    @staticmethod
    def threat_analysis_template(threat_type: str) -> str:
        """Threat analysis prompt template for specific threat types"""
        return f"""
TASK: Conduct detailed {threat_type.upper()} threat analysis based on recent observations and intelligence documents.

THREAT ANALYSIS FORMAT:
1. THREAT IDENTIFICATION AND CLASSIFICATION
   - Specific {threat_type} assets observed
   - Threat classification by capability level
   - Operational status and readiness assessment

2. DOCTRINAL ANALYSIS
   - Apply enemy doctrine from intelligence documents
   - Compare to known {threat_type} employment tactics
   - Assess tactical significance of positioning/movement

3. CAPABILITY ASSESSMENT
   - Weapons systems and engagement capabilities
   - Mobility and survivability characteristics
   - Support requirements and dependencies

4. VULNERABILITY ANALYSIS
   - Technical vulnerabilities of observed systems
   - Tactical vulnerabilities in employment
   - Operational vulnerabilities in support structure

5. THREAT COURSES OF ACTION
   - Most likely enemy courses of action
   - Most dangerous enemy courses of action
   - Timeline estimates for potential actions

6. COUNTERMEASURE RECOMMENDATIONS
   - Immediate response options
   - Long-term mitigation strategies
   - Required capabilities and resources

7. PRIORITY TARGET ANALYSIS
   - High-value targets for engagement
   - Target prioritization criteria
   - Engagement recommendations

ANALYSIS REQUIREMENTS:
- Reference specific observations with MGRS coordinates
- Apply doctrinal knowledge from available documents
- Include confidence levels for assessments
- Provide actionable intelligence for tactical planning

OUTPUT: Comprehensive {threat_type} threat analysis for tactical decision-making.
"""

    @staticmethod
    def patrol_order_template(observation: dict) -> str:
        """Patrol order prompt template for reconnaissance missions"""
        target = observation.get('what', 'Unknown')
        location = observation.get('mgrs', 'Unknown')
        confidence = observation.get('confidence', 0)
        
        return f"""
TASK: Generate reconnaissance patrol order to investigate and confirm observation.

OBSERVATION REQUIRING INVESTIGATION:
- TARGET: {target}
- LOCATION: {location} (MGRS)
- CONFIDENCE: {confidence}% (requires confirmation)

PATROL ORDER FORMAT (5-Paragraph OPORD):
1. SITUATION
   a. Enemy: Based on observation requiring confirmation
   b. Friendly: Current unit positions and support available
   c. Environment: Terrain, weather, visibility conditions

2. MISSION
   - WHO: Patrol designation and composition
   - WHAT: Reconnaissance and confirmation tasks
   - WHEN: Timeline for execution
   - WHERE: Specific location and route
   - WHY: Intelligence requirements and decision support

3. EXECUTION
   a. Concept of Operations: Approach, observe, confirm, report
   b. Tasks to Subordinate Elements: Specific responsibilities
   c. Coordinating Instructions: Control measures and procedures

4. ADMIN/LOGISTICS
   - Personnel and equipment requirements
   - Supply and resupply procedures
   - Medical evacuation procedures
   - Duration and sustainment requirements

5. COMMAND/SIGNAL
   - Command relationships and succession
   - Communication procedures and frequencies
   - Reporting timeline and format
   - Emergency procedures

RECONNAISSANCE REQUIREMENTS:
- Confirm or deny presence of {target}
- Determine exact composition and strength
- Assess activity level and operational status
- Identify vulnerabilities and engagement opportunities
- Report route and positioning information

TACTICAL CONSIDERATIONS:
- Appropriate to {target} threat level and capabilities
- Maintain patrol security and avoid detection
- Include contingency plans for contact situations
- Address extraction and emergency procedures

OUTPUT: Complete patrol order ready for briefing and execution.
"""

# Example prompt customization functions
def customize_frago_for_armor(observation: dict) -> str:
    """Customize FRAGO template specifically for armor threats"""
    base_prompt = MilitaryPromptTemplates.frago_template(observation)
    
    armor_addendum = """
ARMOR-SPECIFIC CONSIDERATIONS:
- Anti-tank weapon deployment and positioning
- Obstacle emplacement and channeling techniques
- Aviation support for armor engagement
- Logistics vulnerabilities of armored formations
- Mobility corridors and choke points
"""
    
    return base_prompt + armor_addendum

def customize_telegram_for_priority(observation: dict, priority: str = "HIGH") -> str:
    """Customize Telegram template for specific priority levels"""
    base_prompt = MilitaryPromptTemplates.telegram_alert_template(observation)
    
    priority_guidance = f"""
PRIORITY LEVEL: {priority}
- HIGH: Immediate command notification required
- MEDIUM: Standard tactical reporting timeline  
- LOW: Routine intelligence update format
"""
    
    return base_prompt + priority_guidance

if __name__ == "__main__":
    # Example usage of prompt templates
    test_obs = {
        'what': 'T-72 Tank',
        'mgrs': '35VLG8475672108',
        'amount': 3,
        'confidence': 95,
        'time_formatted': '142315Z OCT 25',
        'observer_signature': 'Alpha-6',
        'unit': 'Recon Team Alpha'
    }
    
    print("📋 Military Prompt Templates Demo")
    print("=" * 50)
    
    print("\n1. FRAGO TEMPLATE:")
    print(MilitaryPromptTemplates.frago_template(test_obs)[:300] + "...")
    
    print("\n2. TELEGRAM TEMPLATE:")
    print(MilitaryPromptTemplates.telegram_alert_template(test_obs)[:300] + "...")
    
    print("\n3. INTELLIGENCE SUMMARY TEMPLATE:")
    print(MilitaryPromptTemplates.intelligence_summary_template()[:300] + "...")