from rest_framework.views import APIView
from rest_framework.response import Response
import requests

class PopularityScoreView(APIView):
    def post(self, request):
        text = request.data.get("text", "")
        try:
            # talk to popularity microservice
            r = requests.post("http://popularity:9001/predict", json={"text": text})
            return Response(r.json(), status=r.status_code)
        except requests.RequestException as e:
            return Response({"error": str(e)}, status=500)

class SafetyScoreView(APIView):
    def post(self, request):
        text = request.data.get("text", "")
        try:
            # talk to safety microservice
            r = requests.post("http://safety:9002/predict", json={"text": text})
            return Response(r.json(), status=r.status_code)
        except requests.RequestException as e:
            return Response({"error": str(e)}, status=500)