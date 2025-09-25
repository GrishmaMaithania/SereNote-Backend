from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
import os
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import subprocess
from django.views.decorators.csrf import csrf_exempt


# --- Import your processing functions ---
from .chord_analyzer import detect_chords
from .detect_key import detect_key


class DetectScaleView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file uploaded"}, status=400)

        upload_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.name)

        with open(file_path, "wb+") as f:
            for chunk in file.chunks():
                f.write(chunk)

        try:
            result = detect_key(file_path)
            return Response({"scale": result})
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)


class DetectChordsView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file uploaded"}, status=400)

        upload_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.name)

        with open(file_path, "wb+") as f:
            for chunk in file.chunks():
                f.write(chunk)

        try:
            result = detect_chords(file_path, detect_key_fn=detect_key)
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

@csrf_exempt
def detect_from_youtube_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    url = None

    # Parse JSON body
    if request.content_type == "application/json":
        try:
            data = json.loads(request.body.decode("utf-8"))
            url = data.get("url")
        except Exception:
            pass

    # Fallback: form-data
    if not url:
        url = request.POST.get("url")

    if not url:
        return JsonResponse({"error": "URL not provided"}, status=400)

    try:
        # Download YouTube audio using yt-dlp
        output_file = "downloaded_audio.mp3"
        command = [
            "yt-dlp",
            "-x", "--audio-format", "mp3",
            "-o", output_file,
            url
        ]
        subprocess.run(command, check=True, capture_output=True, text=True)

        # Run your existing detect_key
        detected_key = detect_key(output_file)

        # Clean up
        if os.path.exists(output_file):
            os.remove(output_file)

        return JsonResponse({"key": detected_key})

    except subprocess.CalledProcessError as e:
        return JsonResponse({"error": f"yt-dlp error: {e.stderr}"}, status=500)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
@csrf_exempt
def detect_chords_from_youtube_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    url = None
    if request.content_type == "application/json":
        try:
            data = json.loads(request.body.decode("utf-8"))
            url = data.get("url")
        except Exception:
            pass
    if not url:
        url = request.POST.get("url")
    if not url:
        return JsonResponse({"error": "URL not provided"}, status=400)

    try:
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        os.makedirs(upload_dir, exist_ok=True)
        output_file = os.path.join(upload_dir, "youtube_audio.mp3")

        # download audio
        command = [
            "yt-dlp", "-x", "--audio-format", "mp3",
            "-o", output_file, url
        ]
        subprocess.run(command, check=True, capture_output=True, text=True)

        # detect chords
        result = detect_chords(output_file, detect_key_fn=detect_key)

        # cleanup
        if os.path.exists(output_file):
            os.remove(output_file)

        return JsonResponse(result)

    except subprocess.CalledProcessError as e:
        return JsonResponse({"error": f"yt-dlp error: {e.stderr}"}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
