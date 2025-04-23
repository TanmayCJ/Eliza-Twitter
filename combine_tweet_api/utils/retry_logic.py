def build_retry_prompt(reason, previous_tweet):
    """
    Builds a prompt for the LLM to retry generating a tweet after rejection.
    
    Args:
        reason (str): The reason for rejection ('safety' or 'popularity')
        previous_tweet (str): The previously rejected tweet
        
    Returns:
        str: A formatted prompt for the LLM to generate a new tweet
    """
    # Basic safety issue
    if reason == "safety":
        issue_description = "it may contain content that could be controversial or unsafe"
        specific_guidance = """
        - Focus on scientifically verified facts
        - Remove any politically charged language
        - Avoid making accusations against specific companies or individuals
        - Frame issues as opportunities for improvement rather than criticisms
        - Use neutral, professional language
        """
    elif reason == "popularity":
        issue_description = "it may not resonate well with our audience or lacks engagement potential"
        specific_guidance = """
        - Include a specific, actionable data point
        - Add a clear call to action
        - Frame the issue in terms people care about (health, future, economy)
        - Be direct and impactful
        - Use more engaging, vivid language while remaining factual
        """
    else:
        issue_description = f"it has issues related to {reason}"
        specific_guidance = """
        - Focus on clear, verifiable information
        - Keep the message concise and direct
        - Emphasize the climate action aspect
        - Include no more than 2 relevant hashtags
        """
    
    return f"""
You are CarbonSustain, a data-driven climate voice on Twitter.
Your tweets are fact-first, call out greenwashing, and drive climate accountability.
Use stats, avoid fluff. Always aim to educate or provoke real action.

You previously wrote:
"{previous_tweet}"

But it was rejected because: {issue_description}

Specific guidelines for improvement:
{specific_guidance}

Do not include URLs or web links in your revised tweet - they will be added automatically.
Keep your response under 240 characters to allow room for links.

Rewrite it to stay in character and address the issue.
Tweet:"""
