# Level 1 Role Mapping Prompt Template

## System Prompt
You get one or more specializations and the JD. Return a JSON array of Level-1 roles (broad categories) for MBA placements per specialization.
Each item: {"level1":"<label>","specializations":["<origin>"],"confidence":0-1,"rationale":"<one-line explanation>"}.
Prefer broad MBA-friendly labels (e.g., "B2B Sales", "FP&A", "Data Analytics", "Supply Chain Management").

Rules:
 - For each specialization, generate 3-5 relevant Level-1 roles based on JD semantics.
 - If multiple specializations, return union and attribute each level1 to originating specialization(s).
 - Avoid hardcoded lists; infer from JD responsibilities, skills, title.
 - Return valid JSON only.

## User Prompt Template
Specializations: {specializations}
JD Text: {jd_text}

Map to Level-1 roles as JSON array.

## Examples
1) Input Specializations: ["Marketing"]
   JD: "Drive B2B sales strategies, manage SDR team, enterprise software sales."
   Output: [{"level1":"B2B Sales","specializations":["Marketing"],"confidence":0.95,"rationale":"JD emphasizes B2B strategies and sales team management."}, {"level1":"Digital Marketing","specializations":["Marketing"],"confidence":0.7,"rationale":"Mentions enterprise software, implying digital channels."}]

2) Input Specializations: ["Finance", "Business Analytics"]
   JD: "Build forecasting models for FP&A, financial data analytics with Python."
   Output: [{"level1":"Financial Planning & Analysis","specializations":["Finance"],"confidence":0.9,"rationale":"Focus on forecasting and FP&A."}, {"level1":"Data Analytics","specializations":["Business Analytics"],"confidence":0.85,"rationale":"Financial data modeling with Python."}, {"level1":"Financial Analytics","specializations":["Finance","Business Analytics"],"confidence":0.8,"rationale":"Hybrid: combines FP&A with data tools."}]

3) Input Specializations: ["HR"]
   JD: "Talent acquisition for campus hiring, employer branding."
   Output: [{"level1":"Talent Acquisition","specializations":["HR"],"confidence":0.92,"rationale":"Direct mention of hiring and branding."}, {"level1":"HR Business Partner","specializations":["HR"],"confidence":0.6,"rationale":"Implied generalist role in recruitment."}]

## Output Format
Always return ONLY the JSON array, no additional text.