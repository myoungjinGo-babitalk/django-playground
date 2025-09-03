import os
import django

def pytest_configure():
    """
    pytest 실행 전 Django 환경을 초기화합니다.
    
    DJANGO_SETTINGS_MODULE 환경 변수가 설정되어 있지 않으면 'playground.settings'로 설정한 뒤 django.setup()을 호출하여 Django 설정과 앱 레지스트리를 초기화합니다. 이미 설정된 환경 변수는 덮어쓰지 않으며, django.setup()에서 발생하는 예외는 그대로 전파됩니다.
    """
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playground.settings')
    django.setup()