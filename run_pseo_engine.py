import os
import requests
import json
import time

OPENROUTER_API_KEY = "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"

AFFILIATE_LINKS = {
    "enterprise_compliance": "[Vanta - Enterprise AI Compliance Automation](https://vanta.com/?aff=weeklyai)",
    "cloud_security": "[Drata - Continuous Cloud Security](https://drata.com/?aff=weeklyai)",
    "data_loss_prevention": "[Nightfall - AI Data Loss Prevention](https://nightfall.ai/?aff=weeklyai)"
}

CTA_BLOCK = """
<div style="margin-top: 50px; padding: 30px; background-color: #1a1a1a; border-left: 4px solid #00ffcc; border-radius: 8px;">
    <h3 style="color: #00ffcc; margin-top: 0;">Is your enterprise healthcare data secure enough for AI deployment?</h3>
    <p style="color: #e5e5e5; font-size: 1.1em; line-height: 1.6;">Don't risk a $7M breach or HIPAA violation. Book a free, confidential AI Infrastructure Audit with our vetted engineering partners to assess your readiness and build a compliant, on-premise AI solution.</p>
    <a href="mailto:Felix@theweeklyaiedge.com?subject=AI Infrastructure Audit Request" style="display: inline-block; background-color: #00ffcc; color: #0a0a0a; padding: 12px 24px; text-decoration: none; font-weight: bold; border-radius: 4px; margin-top: 15px;">Book Confidential Audit Here</a>
</div>
"""

def call_openrouter(messages, model="meta-llama/llama-3-8b-instruct"):
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    data = {"model": model, "messages": messages, "temperature": 0.5}
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    return f"Error: {response.status_code} - {response.text}"

def generate_article_batch(topics):
    urls = []
    
    system_prompt = f"""
    You are an elite B2B technical writer targeting CTOs and VPs of Engineering.
    Write a 800-word SEO-optimized article on the provided topic. 
    Format in clean HTML (just the content inside <body> tags, structured with <h1>, <h2>, and <p>).
    
    IMPORTANT: You must seamlessly embed the following 3 contextual affiliate links inside your <body> text where relevant:
    1. {AFFILIATE_LINKS['enterprise_compliance']}
    2. {AFFILIATE_LINKS['cloud_security']}
    3. {AFFILIATE_LINKS['data_loss_prevention']}
    Convert the markdown links provided above into proper HTML <a href="..."> tags.
    Tone: Authoritative, pragmatic, financially-driven. Focus on ROI, risk-mitigation, and open-source alternatives.
    """

    for idx, t in enumerate(topics):
        print(f"Generating article for topic {idx+1}: {t}...")
        article_content = call_openrouter([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Topic: {t}"}
        ])
        
        slug = t.lower().replace(' ', '-').replace(':', '').replace('--', '-')
        filename = f"{slug}.html"
        
        final_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{t} | The Weekly AI Edge</title>
    <style>
        body {{ background-color: #0a0a0a; color: #e5e5e5; font-family: 'Inter', sans-serif; padding: 40px; line-height: 1.6; max-width: 800px; margin: 0 auto; }}
        h1, h2, h3 {{ color: #00ffcc; margin-top:30px; }}
        a {{ color: #00ffcc; font-weight: bold; text-decoration: none; border-bottom: 1px dotted #00ffcc; }}
        .container {{ background: #111; padding: 40px; border-radius: 12px; border: 1px solid #333; }}
        ul {{ color: #e5e5e5; }}
    </style>
</head>
<body>
<div class="container">
    <a href="../index.html" style="text-decoration:none; border:none; font-size:14px;">&larr; Back to Home</a>
    {article_content}
    {CTA_BLOCK}
</div>
</body>
</html>
"""
        with open(f"articles/{filename}", 'w') as f:
            f.write(final_html)
            
        urls.append(f"articles/{filename}")
        time.sleep(2)
        
    return urls

if __name__ == "__main__":
    if not os.path.exists('articles'):
        os.makedirs('articles')
    niche_topics = [
        "How open source AI models replace expensive SaaS for HIPAA compliant healthcare",
        "The hidden cost of cloud dependent AI in enterprise healthcare data privacy"
    ]
    urls = generate_article_batch(niche_topics)
    print("Batch finished:", urls)