from api.models import CarbonTruthTweet, CarbonRantTweet

class DatabaseManager:
    """Use Django ORM for database operations"""
    @staticmethod
    def get_latest_entries():
        carbon = CarbonTruthTweet.objects.values('content').first()
        rant = CarbonRantTweet.objects.values('content').first()
        return {
            'carbon_tweet': {
                'content': carbon['content'] if carbon else None
            },
            'rant_tweet': {
                'content': rant['content'] if rant else None
            }
        }
