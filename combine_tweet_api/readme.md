# 1. Create a virtual environment
python -m venv venv

# 2. Activate the virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Make and apply migrations
python manage.py makemigrations
python manage.py migrate combine_tweet --fake-initial

# 5. Create .env file to add database and api credentials

# 6. Run the Django dev server
python manage.py runserver
