from django.apps import AppConfig


class CrawlingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "crawling"

    def ready(self):
        """앱 초기화 시 크롤링 스케줄러 시작"""
        # 개발 환경에서 두 번 실행되는 것 방지
        import os
        if os.environ.get('RUN_MAIN') != 'true':
            from .tasks import scheduler
            scheduler.start()
