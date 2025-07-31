from django.http import StreamingHttpResponse, Http404
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from utils.aes_crypto import decrypt_file_for_user
import os


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stream_encrypted_video(request, filename):
    encrypted_path = os.path.join('media/encrypted', filename)
    
    if not os.path.exists(encrypted_path):
        raise Http404("Video not found")

    decrypted_data = decrypt_file_for_user(encrypted_path)

    response = StreamingHttpResponse(
        iter([decrypted_data]),  
        content_type='video/mp4'
    )
    response['Content-Disposition'] = f'inline; filename="{filename[:-4]}"'
    return response
