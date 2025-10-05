#!/usr/bin/env python3
"""
DefHack FRAGO and INTREP Prompt Engineering Guide
Complete guide to customizing military LLM prompts
"""

print("""
🎯 DefHack FRAGO & INTREP Prompt Engineering Guide
==================================================

📁 PROMPT LOCATIONS & ARCHITECTURE:
===================================

1. 📋 FRAGO (Fragmentary Orders) Generation
   ----------------------------------------
   PRIMARY FILE: military_operations_integration.py
   FUNCTION: DefHackMilitaryOperations.process_new_observation()
   LINE: ~77-95 (frago_prompt variable)
   
   BACKUP FILE: military_llm_functions.py  
   FUNCTION: DefHackMilitaryLLM.generate_frago_order()
   LINE: ~35-65 (frago_query variable)
   
   TEMPLATE FILE: military_prompt_templates.py
   FUNCTION: MilitaryPromptTemplates.frago_template()
   LINE: ~10-50

2. 📊 INTREP (Intelligence Reports) Generation  
   --------------------------------------------
   PRIMARY FILE: military_operations_integration.py
   FUNCTION: DefHackMilitaryOperations.generate_daily_intelligence_summary()
   LINE: ~155-185 (intel_prompt variable)
   
   BACKUP FILE: military_llm_functions.py
   FUNCTION: DefHackMilitaryLLM.generate_24h_intelligence_report()  
   LINE: ~140-180 (intel_query variable)
   
   TEMPLATE FILE: military_prompt_templates.py
   FUNCTION: MilitaryPromptTemplates.intelligence_summary_template()
   LINE: ~80-125

🔧 PROMPT ENGINEERING WORKFLOW:
==============================

STEP 1: Choose Your Editing Approach
------------------------------------
OPTION A - Quick Production Changes:
  Edit: military_operations_integration.py (lines 77-95 for FRAGO, 155-185 for INTREP)
  
OPTION B - Template-Based Development:
  Edit: military_prompt_templates.py (modify templates, then update integration)
  
OPTION C - Advanced Development:
  Edit: military_llm_functions.py (full control over prompt logic)

STEP 2: Understand the Prompt Structure
---------------------------------------
Each prompt has these components:
  - CONTEXT INJECTION (observation data, document references)
  - FORMAT REQUIREMENTS (military standards, structure)
  - TACTICAL CONSIDERATIONS (threat-specific guidance)
  - OUTPUT SPECIFICATIONS (length, style, citations)

STEP 3: Test Your Changes
-------------------------
  Run: python military_operations_integration.py
  Or:  python test_military_llm.py

📋 FRAGO PROMPT ARCHITECTURE:
=============================

CURRENT FRAGO PROMPT STRUCTURE:
------------------------------
File: military_operations_integration.py, lines 77-95

```python
frago_prompt = f'''
Generate a brief FRAGO for immediate response to: {target} (x{amount}) at {location} with {confidence}% confidence.

Format:
FRAGO [NUMBER] - [TARGET] RESPONSE
1. SITUATION: {target} observed at {location}
2. MISSION: [Unit] will [action] to [purpose]
3. EXECUTION: 
   - Immediate actions (0-30 min)
   - Follow-up actions (30 min - 2 hours)
4. TIMELINE: Specific milestones
5. COORDINATION: Communication and reporting

Keep under 250 words for rapid dissemination.
'''
```

FRAGO CUSTOMIZATION POINTS:
---------------------------
A. THREAT-SPECIFIC RESPONSES:
   - Add if/else logic for different threat types
   - Customize actions based on target (armor vs infantry vs aircraft)
   
B. CONFIDENCE-BASED ACTIONS:
   - High confidence (90%+): Immediate engagement procedures
   - Medium confidence (70-89%): Reconnaissance and confirmation
   - Low confidence (<70%): Monitoring and additional collection
   
C. UNIT-SPECIFIC PROCEDURES:
   - Customize based on friendly unit capabilities
   - Include specific call signs, frequencies, boundaries

📊 INTREP PROMPT ARCHITECTURE:
==============================

CURRENT INTREP PROMPT STRUCTURE:
--------------------------------
File: military_operations_integration.py, lines 155-185

```python
intel_prompt = f'''
Generate a professional 24-hour intelligence summary:

OBSERVATIONS ({len(observations)} total):
{chr(10).join(obs_list)}

FORMAT:
1. EXECUTIVE SUMMARY (2-3 sentences)
2. KEY OBSERVATIONS (priority threats)
3. PATTERN ANALYSIS (geographic/temporal patterns)
4. THREAT ASSESSMENT (capabilities and intentions)
5. RECOMMENDATIONS (immediate actions and collection priorities)

Use proper military intelligence format. Reference specific observations and apply doctrinal knowledge from available documents about enemy tactics.

Keep under 500 words for briefing purposes.
'''
```

INTREP CUSTOMIZATION POINTS:
----------------------------
A. INTELLIGENCE FOCUS AREAS:
   - Emphasize specific threat types (BTG analysis, logistics, C2)
   - Add specialized sections (SIGINT, GEOINT, HUMINT)
   
B. ANALYSIS DEPTH:
   - Tactical level (immediate threats, local patterns)
   - Operational level (campaign analysis, strategic implications)
   - Strategic level (long-term trends, policy implications)
   
C. AUDIENCE CUSTOMIZATION:
   - Company level: Tactical focus, immediate actions
   - Battalion level: Operational coordination, resource allocation  
   - Brigade level: Strategic planning, campaign assessment

🛠️ PROMPT MODIFICATION EXAMPLES:
================================

EXAMPLE 1: Enhanced FRAGO for Armor Threats
-------------------------------------------
Add this logic to military_operations_integration.py after line 90:

```python
# Armor-specific enhancements
if 'tank' in target.lower() or 't-' in target.lower():
    frago_prompt += f'''
    
ARMOR-SPECIFIC CONSIDERATIONS:
- Deploy anti-tank teams to engagement positions
- Coordinate with aviation assets for top-attack munitions
- Establish observation posts on likely armor approaches
- Prepare obstacle emplacement in mobility corridors
- Brief Rules of Engagement for armor engagement
'''
```

EXAMPLE 2: Pattern-Enhanced INTREP
----------------------------------
Replace intel_prompt in military_operations_integration.py with:

```python
intel_prompt = f'''
Generate comprehensive 24-hour intelligence summary with advanced pattern analysis:

OBSERVATIONS ({len(observations)} total):
{chr(10).join(obs_list)}

REQUIRED ANALYSIS SECTIONS:
1. EXECUTIVE SUMMARY - Key findings and commander's critical information requirements
2. THREAT BY WARFIGHTING FUNCTION:
   - Movement & Maneuver: Observed repositioning and tactical movement
   - Intelligence: Enemy reconnaissance and surveillance activities  
   - Fires: Indirect fire assets and target acquisition
   - Protection: Enemy defensive preparations and force protection
   - Sustainment: Logistics activities and supply operations
   - Command & Control: Communications and leadership activities
3. PATTERN ANALYSIS:
   - Temporal: Time-based activity patterns and operational rhythm
   - Spatial: Geographic clustering and area of operations analysis
   - Tactical: Doctrinal conformity and tactical signature analysis
4. DOCTRINAL ASSESSMENT:
   - Apply BTG doctrine from available intelligence documents
   - Compare observed activities to known enemy tactics, techniques, procedures
   - Assess enemy course of action development
5. INTELLIGENCE GAPS & PIR:
   - Critical information gaps requiring immediate collection
   - Priority Intelligence Requirements for next 24 hours
   - Recommended collection assets and methods
6. RECOMMENDATIONS:
   - Immediate actions for force protection and tactical advantage
   - Intelligence collection guidance
   - Coordination requirements with adjacent units

Apply Russian BTG doctrine from uploaded documents. Include specific document citations.
Maintain professional intelligence community standards.
Maximum 750 words for staff briefing.
'''
```

🎯 ADVANCED PROMPT ENGINEERING TECHNIQUES:
==========================================

1. DYNAMIC PROMPT SELECTION:
   -------------------------
   ```python
   def get_frago_prompt(target, threat_level, unit_type):
       if threat_level == "HIGH" and "armor" in target.lower():
           return armor_high_threat_prompt
       elif "recon" in target.lower():
           return reconnaissance_response_prompt
       else:
           return standard_frago_prompt
   ```

2. CONTEXTUAL DOCUMENT INJECTION:
   --------------------------------
   ```python
   # Add relevant doctrine to prompts
   relevant_docs = search_documents(target_type)
   prompt += f"\\nAPPLY DOCTRINE FROM: {relevant_docs}"
   ```

3. CONFIDENCE-WEIGHTED RESPONSES:
   --------------------------------
   ```python
   if confidence >= 90:
       action_verbs = ["ENGAGE", "ATTACK", "DESTROY"]
   elif confidence >= 70:
       action_verbs = ["INVESTIGATE", "CONFIRM", "OBSERVE"]  
   else:
       action_verbs = ["MONITOR", "TRACK", "REPORT"]
   ```

📝 PROMPT TESTING & VALIDATION:
===============================

TESTING WORKFLOW:
----------------
1. Modify prompts in chosen file
2. Run test: python test_military_llm.py
3. Evaluate output for:
   - Military format compliance
   - Tactical relevance  
   - Actionable intelligence
   - Appropriate classification handling
4. Iterate and refine

VALIDATION CRITERIA:
-------------------
✅ FRAGO Validation:
   - 5-paragraph format maintained
   - Clear mission statement
   - Specific timelines and coordination
   - Appropriate to threat level
   
✅ INTREP Validation:
   - Professional intelligence format
   - Cites relevant documents
   - Actionable recommendations
   - Appropriate confidence assessments

🔄 CONTINUOUS IMPROVEMENT:
=========================

FEEDBACK LOOP:
--------------
1. Deploy prompt changes
2. Collect user feedback on output quality
3. Monitor LLM performance metrics
4. Analyze tactical relevance of generated orders
5. Refine prompts based on operational experience

VERSIONING:
-----------
- Keep backup copies of working prompts
- Document changes with tactical rationale
- Test extensively before operational deployment

🎉 START PROMPT ENGINEERING!
============================

PRIMARY FILES TO EDIT:
----------------------
1. military_operations_integration.py (PRODUCTION - lines 77-95, 155-185)
2. military_prompt_templates.py (TEMPLATES - for structured development)
3. military_llm_functions.py (ADVANCED - for complex logic)

QUICK START:
-----------
1. Edit military_operations_integration.py
2. Modify the frago_prompt or intel_prompt variables
3. Run: python military_operations_integration.py
4. Test with real sensor data
5. Iterate until satisfied

Your prompts control tactical decision-making - engineer them carefully! 🎯
""")

if __name__ == "__main__":
    print("\\n🚀 Ready to fine-tune your military LLM prompts!")
    print("Start with military_operations_integration.py for quick changes!")