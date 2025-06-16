# Standard Library
import requests
from bs4 import BeautifulSoup

class TwitterTrendsService:
    def __init__(self):
        self.url = "https://trends24.in/united-states/los-angeles/"
        self.headers = {'User-Agent': 'Mozilla/5.0'}
    
    def get_timeframes(self):
        """Get all available timeframes from the trends site"""
        response = requests.get(self.url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all containers
        containers = soup.find_all('div', class_='list-container')
        
        # Store all timeframe titles in a list
        timeframes = []
        for idx, container in enumerate(containers):
            title_tag = container.find('h3', class_='title')
            if title_tag:
                timeframes.append({
                    "index": idx,
                    "name": title_tag.text.strip()
                })
                
        return timeframes
    
    def get_trends(self, selected_index=0):
        """Get trends for a specific timeframe index"""
        response = requests.get(self.url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all containers
        containers = soup.find_all('div', class_='list-container')
        
        # Store all timeframe titles in a list
        timeframes = []
        for container in containers:
            title_tag = container.find('h3', class_='title')
            if title_tag:
                timeframes.append(title_tag.text.strip())
        
        # Validate the selected index
        if selected_index < 0 or selected_index >= len(containers):
            return {"error": "Invalid index"}
        
        selected_container = containers[selected_index]
        
        # Extract the trends
        trends_list = []
        trends = selected_container.find_all('li')
        for trend in trends:
            trends_list.append(trend.text.strip())
        
        return {
            "timeframe": timeframes[selected_index],
            "trends": trends_list
        }