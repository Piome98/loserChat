from django.core.management.base import BaseCommand
from chats.models import ChatMessage, ChatRoom

class Command(BaseCommand):
    help = '오래된 메시지를 정리하여 각 토론방의 메시지를 최대 500개로 유지합니다.'

    def handle(self, *args, **options):
        # 각 일반 토론방 순회
        rooms = ChatRoom.objects.all()
        for room in rooms:
            messages_count = ChatMessage.objects.filter(chatroom=room).count()
            if messages_count > 500:
                # 가장 오래된 메시지부터 삭제
                oldest_messages = ChatMessage.objects.filter(chatroom=room).order_by('created_at')[:messages_count-500]
                deleted_count = oldest_messages.count()
                oldest_messages.delete()
                self.stdout.write(self.style.SUCCESS(f'토론방 "{room.name}"에서 {deleted_count}개의 오래된 메시지를 삭제했습니다.'))
        
        # 패잔병 토론방 메시지 정리
        loser_messages_count = ChatMessage.objects.filter(room_type='loser').count()
        if loser_messages_count > 500:
            # 가장 오래된 메시지부터 삭제
            oldest_loser_messages = ChatMessage.objects.filter(room_type='loser').order_by('created_at')[:loser_messages_count-500]
            deleted_count = oldest_loser_messages.count()
            oldest_loser_messages.delete()
            self.stdout.write(self.style.SUCCESS(f'패잔병 토론방에서 {deleted_count}개의 오래된 메시지를 삭제했습니다.'))
        
        self.stdout.write(self.style.SUCCESS('메시지 정리가 완료되었습니다.'))
