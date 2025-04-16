# accounts/serializers.py
# 회원가입시 유저 데이터 저장 검증 및 저장

from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password

class UserSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True) # 비밀번호 확인 필드 추가

    class Meta:
        model = User
        fields = ['username', 'nickname', 'password', 'password2']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "비밀번호가 일치하지 않습니다."})
        return attrs

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            nickname=validated_data.get('nickname', '')
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
