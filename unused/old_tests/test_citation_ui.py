#!/usr/bin/env python3
"""
Test script for the citation UI functionality
"""

def extract_skills_from_answer(answer_text: str):
    """Extract skills data from answer text for citation display"""
    skills = []

    # Look for patterns like "Skill Name: ... Cited By Companies: ..."
    lines = answer_text.split('\n')
    current_skill = None
    companies = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for skill name pattern
        if line.startswith('**') and '**' in line[2:]:
            # Extract skill name from bold text
            skill_part = line.split('**')[1]
            if ':' in skill_part:
                skill_name = skill_part.split(':')[0].strip()
                current_skill = skill_name
                companies = []
        elif 'Cited By Companies:' in line or 'Cited by:' in line:
            # Extract companies
            if ':' in line:
                companies_text = line.split(':', 1)[1].strip()
                # Split by commas and clean up
                companies = [c.strip() for c in companies_text.split(',') if c.strip()]
        elif 'Relevant Specializations:' in line:
            if current_skill and companies:
                specializations = []
                if ':' in line:
                    spec_text = line.split(':', 1)[1].strip()
                    specializations = [s.strip() for s in spec_text.split(',') if s.strip()]

                skills.append({
                    'skill': current_skill,
                    'companies': companies,
                    'specializations': specializations
                })
                current_skill = None
                companies = []

    # Handle case where we have skill and companies but no specializations line
    if current_skill and companies:
        skills.append({
            'skill': current_skill,
            'companies': companies,
            'specializations': []
        })

    return skills

def test_extract_skills():
    """Test the skill extraction function"""
    sample_answer = """
**Communication Execution**
Cited By Companies: Masters' Union, Alstom, Tap Academy
Relevant Specializations: Marketing, HR, Operations

**Data Analytics**
Cited By Companies: Accorian, Masters' Union
Relevant Specializations: Business Analytics, Finance
"""

    skills = extract_skills_from_answer(sample_answer)
    print("Extracted skills:")
    for skill in skills:
        print(f"- {skill['skill']}: {skill['companies']}")

    assert len(skills) == 2
    assert skills[0]['skill'] == 'Communication Execution'
    assert 'Masters\' Union' in skills[0]['companies']
    print("✅ Skill extraction test passed!")

if __name__ == "__main__":
    test_extract_skills()