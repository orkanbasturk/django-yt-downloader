from django.shortcuts import render
from django.http import HttpResponse, FileResponse, JsonResponse
from .forms import YouTubeForm
import yt_dlp
import os
from django.conf import settings
from pathlib import Path
import subprocess
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


# İndirme ilerlemesini izlemek için kanca fonksiyonu
def my_hook(d):
    if d['status'] == 'downloading':
        if 'total_bytes' in d and 'downloaded_bytes' in d:
            total_bytes = d['total_bytes']
            downloaded_bytes = d['downloaded_bytes']
            percentage = (downloaded_bytes / total_bytes) * 100
            progress_message = f"Video İndiriliyor: %{percentage:.2f} - Süre: {d.get('elapsed', 0)}"
        else:
            progress_message = "Video İndiriliyor: %0 - Süre: 0"

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'progress_group',
            {
                'type': 'send_progress',
                'message': progress_message
            }
        )
    elif d['status'] == 'finished':
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'progress_group',
            {
                'type': 'send_progress',
                'message': 'Video Dönüştürülüyor'
            }
        )


def index(request):
    if request.method == 'POST':
        form = YouTubeForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            quality = form.cleaned_data['quality']
            try:
                temp_video_path = os.path.join(settings.MEDIA_ROOT, 'temp_video')

                format_option = 'bestvideo+bestaudio' if quality == 'best' else \
                    'worstvideo+worstaudio' if quality == 'worst' else \
                        'bestvideo[height<=720]+bestaudio' if quality == 'high' else \
                            'bestvideo[height<=480]+bestaudio' if quality == 'medium' else \
                                'bestvideo[height<=360]+bestaudio'

                ydl_opts = {
                    'format': format_option,
                    'outtmpl': temp_video_path + '.%(ext)s',
                    'merge_output_format': 'mp4',
                    'progress_hooks': [my_hook],
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(url, download=False)
                    video_title = info_dict.get('title', None)
                    ydl.download([url])

                temp_video_file = temp_video_path + '.mp4'
                if not os.path.isfile(temp_video_file):
                    temp_video_file = temp_video_path + '.mkv'

                final_video_path = os.path.join(settings.MEDIA_ROOT, f'{video_title}.mp4')

                # FFmpeg ile videoyu yeniden kodlama ve HLS parçalarını birleştirme
                ffmpeg_command = [
                    'ffmpeg', '-i', temp_video_file, '-c:v', 'libx264', '-preset', 'fast', '-crf', '28', '-c:a', 'aac',
                    '-b:a', '128k', final_video_path
                ]
                subprocess.run(ffmpeg_command, check=True)

                response = FileResponse(open(final_video_path, 'rb'), as_attachment=True, filename=f'{video_title}.mp4')
                return response
            except Exception as e:
                return HttpResponse(f'Hata: {e}')
    else:
        form = YouTubeForm()

    return render(request, 'downloader/index.html', {'form': form})


def fetch_info(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        url = data.get('url')
        if url:
            try:
                with yt_dlp.YoutubeDL() as ydl:
                    info_dict = ydl.extract_info(url, download=False)
                    video_title = info_dict.get('title', 'Başlık bulunamadı')
                    thumbnail_url = info_dict.get('thumbnail', '')
                    return JsonResponse({'title': video_title, 'thumbnail': thumbnail_url})
            except Exception as e:
                return JsonResponse({'error': str(e)})
    return JsonResponse({'error': 'Geçersiz istek'}, status=400)
