from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from notifications.models import Notification

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_notification(request, notification_id):
    try:
        notif = Notification.objects.get(id=notification_id, recipient=request.user)
        notif.delete()
        return Response({"success": True})
    except Notification.DoesNotExist:
        return Response({"success": False, "error": "Not found"}, status=404)
