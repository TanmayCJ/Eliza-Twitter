from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os
import re

persona = """
You are CarbonSustain, a data-driven climate voice on Twitter.
Your tweets are fact-first, call out greenwashing, and drive climate accountability.
Use stats, avoid fluff. Always aim to educate or provoke real action.
"""

class TweetLLM:
    def __init__(self, model_path="new/carbonsustain/llm/finetuned-twitter-llm1", device="cuda" if torch.cuda.is_available() else "cpu"):
        # Ensure the model path exists
        if not os.path.exists(model_path):
            raise ValueError(f"Model path '{model_path}' does not exist.")
            
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(model_path).to(device)
        self.device = device

    def generate(self, prompt, max_tokens=60, temperature=0.7):
        full_prompt = f"{persona.strip()}\n\nPrompt: {prompt}\nTweet:"
        inputs = self.tokenizer(full_prompt, return_tensors="pt").to(self.device)
        
        # Generate with improved parameters for better, more controlled output
        outputs = self.model.generate(
            **inputs, 
            max_new_tokens=max_tokens, 
            do_sample=True, 
            top_k=50,
            top_p=0.92,
            temperature=temperature,
            no_repeat_ngram_size=3,
            repetition_penalty=1.2
        )
        
        # Get the generated text and clean it
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract just the tweet part (after the prompt)
        if "Tweet:" in generated_text:
            tweet = generated_text.split("Tweet:", 1)[1].strip()
        else:
            tweet = generated_text.replace(full_prompt.strip(), "").strip()
        
        # Post-process the tweet to clean up common issues
        tweet = self._post_process_tweet(tweet)
            
        return tweet
    
    def _post_process_tweet(self, tweet):
        """Clean up the generated tweet to fix common issues"""
        # Remove any instances of "Tweet:" that might have been generated
        tweet = re.sub(r'^Tweet:\s*', '', tweet)
        
        # Fix common hashtag formatting issues (#This should be #This)
        tweet = re.sub(r'#(\w+\s+\w+)', r'#\1', tweet)
        
        # Remove any URL fragments that might have been generated
        # We'll add the real URLs later in the API
        url_pattern = re.compile(r'https?://\S+')
        tweet = url_pattern.sub('', tweet).strip()
        
        # Remove multiple spaces
        tweet = re.sub(r'\s+', ' ', tweet).strip()
        
        # Remove excessive hashtags (keep at most 3)
        hashtags = re.findall(r'#\w+', tweet)
        if len(hashtags) > 3:
            for tag in hashtags[3:]:
                tweet = tweet.replace(tag, '')
        
        # Make sure the tweet is concise
        if len(tweet) > 240:
            tweet = tweet[:237] + "..."
            
        return tweet.strip()
