import os
from typing import Optional

def get_support_policy(topic: str = "general") -> str:
    """
    Retrieves Customer Service Policy and FAQ information.
    Use this to answer user questions about refunds, account management,
    methodology, or privacy.

    Args:
        topic: The specific topic to search for (e.g., "refund", "privacy", "financial advice").
               Defaults to "general" which returns the core principles and TOC.

    Returns:
        Relevant sections of the customer service policy.
    """
    # Locate the policy file relative to the project root
    # Assuming this tool is in src/tools/ and policy is in root/
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    # Assuming src/tools/customer_service.py -> ../../../ -> root
    # Wait, src/tools/customer_service.py -> src/tools/ -> src/ -> root. That's 3 levels up.
    # Original code: 
    # current_dir = os.path.dirname(os.path.abspath(__file__)) (src/tools)
    # project_root = os.path.dirname(os.path.dirname(current_dir)) (root)
    # This was correct: src/tools (dir) -> src (parent) -> root (parent of parent)
    
    # New path is docs/customer-service-policy.md
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    policy_path = os.path.join(project_root, "docs", "customer-service-policy.md")

    try:
        with open(policy_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return "Error: Customer Service Policy file not found."

    topic_lower = topic.lower()

    # If general, return the "Core Principles" and just the headers of the FAQ
    if topic_lower == "general":
        # Extract Core Principles
        principles_start = content.find("## Core Principles")
        faq_start = content.find("## Common Questions & Answers")
        
        if principles_start != -1 and faq_start != -1:
            principles = content[principles_start:faq_start].strip()
            # Just grab the intro of the FAQ section or list headers
            return (
                f"{principles}\n\n"
                "## Available FAQ Topics (ask specifically for details):\n"
                "- Is this financial advice?\n"
                "- How do you find bullish call option setups?\n"
                "- Do you track unusual options flow?\n"
                "- How do I access the full features?\n"
                "- How do I manage my account?\n"
                "- Dashboard loading / missing stock\n"
                "- Referral program\n"
                "- Privacy & Security\n"
            )
        return content[:1000] + "\n... (specify a topic for more)"

    # Simple keyword mapping to sections
    keywords = {
        "financial advice": "Is this financial advice?",
        "legal": "Is this financial advice?",
        "methodology": "How do you find bullish call option setups?",
        "bullish": "How do you find bullish call option setups?",
        "flow": "Do you track unusual options flow?",
        "unusual": "Do you track unusual options flow?",
        "access": "How do I access the full features?",
        "account": "How do I manage my account?",
        "missing": "My dashboard isn't loading or a stock is missing",
        "load": "My dashboard isn't loading or a stock is missing",
        "referral": "How does the referral program work?",
        "feedback": "Handling Negative Feedback",
        "bug": "Handling Negative Feedback",
        "feature": "Handling Feature Requests",
        "privacy": "Data, Privacy, & Security",
        "security": "Data, Privacy, & Security",
        "payment": "How is my payment information handled?",
        "data": "Do you use my stock queries",
    }

    # Check for direct keyword matches
    search_phrase = keywords.get(topic_lower, topic_lower)
    
    # Simple semantic-ish search: find the section containing the phrase
    if search_phrase in content.lower():
        # Find the header roughly associated with this
        lines = content.split('\n')
        result_lines = []
        capturing = False
        
        for line in lines:
            # simple header detection
            if line.startswith("#"):
                if search_phrase in line.lower():
                    capturing = True
                elif capturing and line.startswith("##"):
                    capturing = False
            
            # If we are in a capturing block OR the line contains the search phrase directly
            if capturing or search_phrase in line.lower():
                 # If we found the phrase in a non-header line, capture context around it
                 if not capturing and search_phrase in line.lower():
                     # This is a fallback for when the topic is in the body text
                     return f"Found mention of '{topic}':\n\n{line}\n..."
                 
                 result_lines.append(line)
        
        if result_lines:
            return "\n".join(result_lines)

    # Fallback: If no specific match, return the FAQ section as it covers most issues
    faq_start = content.find("## Common Questions & Answers")
    if faq_start != -1:
         return f"Specific topic '{topic}' not found. Here is the FAQ:\n\n" + content[faq_start:]
    
    return "Could not find relevant policy information. Please contact a human supervisor."
