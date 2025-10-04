#!/usr/bin/env python3
"""
DefHack Prompt Editor
Interactive tool for editing FRAGO and INTREP prompts
"""
import os
from datetime import datetime

def show_current_prompts():
    """Display the current prompts with line numbers"""
    
    print("🔍 CURRENT PROMPTS IN DefHack")
    print("=" * 80)
    
    print("\n📋 FRAGO PROMPT (military_operations_integration.py, lines 71-84)")
    print("-" * 60)
    frago_prompt = '''Generate a brief FRAGO for immediate response to: {target} (x{amount}) at {location} with {confidence}% confidence.

Format:
FRAGO [NUMBER] - [TARGET] RESPONSE
1. SITUATION: {target} observed at {location}
2. MISSION: [Unit] will [action] to [purpose]
3. EXECUTION: 
   - Immediate actions (0-30 min)
   - Follow-up actions (30 min - 2 hours)
4. TIMELINE: Specific milestones
5. COORDINATION: Communication and reporting

Keep under 250 words for rapid dissemination.'''
    
    print(frago_prompt)
    
    print("\n📊 INTREP PROMPT (military_operations_integration.py, lines 124-140)")
    print("-" * 60)
    intrep_prompt = '''Generate a professional 24-hour intelligence summary:

OBSERVATIONS ({len(observations)} total):
{chr(10).join(obs_list)}

FORMAT:
1. EXECUTIVE SUMMARY (2-3 sentences)
2. KEY OBSERVATIONS (priority threats)
3. PATTERN ANALYSIS (geographic/temporal patterns)
4. THREAT ASSESSMENT (capabilities and intentions)
5. RECOMMENDATIONS (immediate actions and collection priorities)

Use proper military intelligence format. Reference specific observations and apply doctrinal knowledge from available documents about enemy tactics.

Keep under 500 words for briefing purposes.'''
    
    print(intrep_prompt)

def create_enhanced_frago_examples():
    """Show enhanced FRAGO prompt examples"""
    
    print("\n🛠️ ENHANCED FRAGO PROMPT EXAMPLES")
    print("=" * 80)
    
    print("\n1. THREAT-SPECIFIC FRAGO (Armor Enhanced)")
    print("-" * 50)
    armor_frago = '''Generate a FRAGO for immediate armor threat response: {target} (x{amount}) at {location} with {confidence}% confidence.

FORMAT:
FRAGO [NUMBER] - ARMOR THREAT RESPONSE
1. SITUATION: {target} observed at {location} - ARMOR THREAT CONFIRMED
2. MISSION: [Unit] will ENGAGE and DESTROY enemy armor to PREVENT breakthrough
3. EXECUTION:
   IMMEDIATE ACTIONS (0-30 min):
   - Deploy Javelin/TOW teams to overwatch positions
   - Alert CAS on station for immediate armor engagement
   - Establish hasty anti-tank obstacles on mobility corridors
   
   FOLLOW-UP ACTIONS (30 min - 2 hours):
   - Conduct BDA and report enemy armor status
   - Reposition AT assets based on enemy movement
   - Coordinate with adjacent units for flank security
   
4. ARMOR-SPECIFIC CONSIDERATIONS:
   - Engage beyond enemy main gun range (>3000m for T-72)
   - Use top-attack munitions to defeat reactive armor
   - Target lead and trail vehicles to create kill zones
   - Coordinate fires to suppress accompanying infantry

5. TIMELINE:
   - AT teams in position: 15 minutes
   - First engagement: 30 minutes
   - BDA report: 45 minutes

6. COORDINATION:
   - CAS freq: 123.45, call sign HAMMER
   - Adjacent units: BRAVO-6 on 456.78
   - Report all engagements to TOC immediately

Keep under 350 words. Include specific anti-armor tactics.'''
    
    print(armor_frago)
    
    print("\n2. CONFIDENCE-BASED FRAGO (High/Medium/Low)")
    print("-" * 50)
    confidence_frago = '''Generate FRAGO based on confidence level: {target} (x{amount}) at {location} with {confidence}% confidence.

CONFIDENCE-BASED RESPONSE:
{confidence_action}

FORMAT:
FRAGO [NUMBER] - {confidence_level} CONFIDENCE RESPONSE
1. SITUATION: {target} observed at {location} - {confidence}% confidence
2. MISSION: [Unit] will {mission_verb} to {mission_purpose}
3. EXECUTION:
   {execution_actions}
4. VERIFICATION REQUIREMENTS:
   {verification_needs}
5. ESCALATION PROCEDURES:
   {escalation_steps}

Adjust response intensity based on confidence level.'''
    
    print(confidence_frago)

def create_enhanced_intrep_examples():
    """Show enhanced INTREP prompt examples"""
    
    print("\n📊 ENHANCED INTREP PROMPT EXAMPLES")
    print("=" * 80)
    
    print("\n1. BTG-FOCUSED INTREP (Doctrinal Analysis)")
    print("-" * 50)
    btg_intrep = '''Generate comprehensive 24-hour intelligence summary with BTG doctrinal analysis:

OBSERVATIONS ({len(observations)} total):
{chr(10).join(obs_list)}

INTELLIGENCE ASSESSMENT FORMAT:
1. EXECUTIVE SUMMARY
   - Commander's Critical Information Requirements (CCIR)
   - Immediate threat assessment and recommended actions
   - Overall enemy situation and intent assessment

2. BTG DOCTRINAL ANALYSIS
   - Apply Russian BTG doctrine from available intelligence documents [D:5][D:6]
   - Compare observed activities to expected BTG deployment patterns
   - Assess BTG phase of operations (reconnaissance, deployment, attack)
   - Identify deviations from doctrine and tactical implications

3. THREAT ANALYSIS BY WARFIGHTING FUNCTION
   - MOVEMENT & MANEUVER: Observed repositioning, tactical formations
   - INTELLIGENCE: Enemy reconnaissance and surveillance signatures  
   - FIRES: Indirect fire preparation, target acquisition activities
   - PROTECTION: Defensive measures, force protection indicators
   - SUSTAINMENT: Logistics signatures, supply line activities
   - COMMAND & CONTROL: Communications patterns, leadership movements

4. PATTERN ANALYSIS
   - TEMPORAL: Activity timing, operational rhythm, peak periods
   - SPATIAL: Geographic clustering, axes of advance, defensive positions
   - TACTICAL: Force ratios, equipment types, capability indicators

5. ENEMY COURSES OF ACTION
   - MOST LIKELY: Based on observed patterns and BTG doctrine
   - MOST DANGEROUS: Worst-case scenarios requiring immediate preparation
   - INDICATORS: Key signatures to watch for COA confirmation

6. INTELLIGENCE GAPS & PIR
   - Critical missing information affecting tactical decisions
   - Priority Intelligence Requirements for next 24 hours
   - Recommended collection methods and assets

7. RECOMMENDATIONS
   - IMMEDIATE ACTIONS: Force protection and tactical positioning
   - INTELLIGENCE OPERATIONS: Collection priorities and methods
   - COORDINATION: Requirements with higher/adjacent units

Apply BTG tactical doctrine from documents. Include specific citations [D:X pY ¶Z].
Professional intelligence format. Maximum 750 words for command briefing.'''
    
    print(btg_intrep)
    
    print("\n2. PATTERN-ENHANCED INTREP (Advanced Analysis)")
    print("-" * 50)
    pattern_intrep = '''Generate advanced pattern-analysis intelligence summary:

OBSERVATIONS ({len(observations)} total):
{chr(10).join(obs_list)}

ADVANCED INTELLIGENCE ANALYSIS:
1. EXECUTIVE SUMMARY - Key patterns and immediate threats

2. MULTI-DOMAIN PATTERN ANALYSIS
   a) TEMPORAL PATTERNS:
      - Peak activity periods and operational rhythm
      - Sequence analysis and predictive indicators
      - Correlation with external events (weather, terrain, operations)
   
   b) SPATIAL PATTERNS:
      - Geographic concentration and dispersion analysis
      - Movement corridors and staging areas
      - Defensive positioning and terrain utilization
   
   c) TACTICAL PATTERNS:
      - Force composition and capability clustering
      - Employment methods and tactical signature analysis
      - Doctrinal conformity assessment

3. PREDICTIVE ANALYSIS
   - Statistical confidence in pattern continuation
   - Anticipated enemy actions based on observed trends
   - Timeline estimates for probable activities

4. ANOMALY DETECTION
   - Deviations from established patterns
   - Unusual activities requiring investigation
   - Potential deception or operational security measures

5. INTELLIGENCE COLLECTION ASSESSMENT
   - Sensor coverage analysis and gaps
   - Collection reliability and confidence trends
   - Recommended adjustments to collection strategy

Apply advanced analytical techniques. Include confidence assessments.
Maximum 600 words with statistical rigor.'''
    
    print(pattern_intrep)

def show_editing_instructions():
    """Show step-by-step editing instructions"""
    
    print("\n✏️ STEP-BY-STEP PROMPT EDITING GUIDE")
    print("=" * 80)
    
    print("""
TO EDIT FRAGO PROMPTS:
---------------------
1. Open: military_operations_integration.py
2. Find line 72: frago_prompt = f'''
3. Replace the content between ''' and '''
4. Test: python military_operations_integration.py

FRAGO LOCATION:
File: military_operations_integration.py
Function: DefHackMilitaryOperations.process_new_observation()
Lines: 72-84

TO EDIT INTREP PROMPTS:
----------------------
1. Open: military_operations_integration.py  
2. Find line 124: intel_prompt = f'''
3. Replace the content between ''' and '''
4. Test: python military_operations_integration.py

INTREP LOCATION:
File: military_operations_integration.py
Function: DefHackMilitaryOperations.generate_daily_intelligence_summary()
Lines: 124-140

TESTING YOUR CHANGES:
--------------------
1. Save your changes
2. Run: python military_operations_integration.py
3. Or: python test_military_llm.py
4. Check output format and tactical relevance
5. Iterate until satisfied

BACKUP YOUR WORKING PROMPTS:
----------------------------
Before major changes, copy your working prompts to a backup file!

ADVANCED CUSTOMIZATION:
----------------------
- Add threat-specific logic with if/else statements
- Include confidence-based response variations
- Integrate document citations dynamically
- Add unit-specific procedures and call signs
""")

def main():
    """Main prompt editing guide"""
    
    print("🎯 DefHack Prompt Engineering Tool")
    print("=" * 80)
    
    show_current_prompts()
    create_enhanced_frago_examples()
    create_enhanced_intrep_examples()
    show_editing_instructions()
    
    print(f"\n🚀 READY TO EDIT PROMPTS!")
    print("=" * 40)
    print("Primary file: military_operations_integration.py")
    print("FRAGO prompt: lines 72-84")
    print("INTREP prompt: lines 124-140")
    print("\nTest with: python military_operations_integration.py")

if __name__ == "__main__":
    main()