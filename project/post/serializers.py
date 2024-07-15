from rest_framework import serializers
from .models import *

class PostSerializer(serializers.ModelSerializer):
    tag = serializers.SerializerMethodField()
    image = serializers.ImageField(use_url=True, required=False)
    comments = serializers.SerializerMethodField(read_only=True)

    def get_comments(self, instance):
        serializer = CommentSerializer(instance.comments, many=True)
        return serializer.data
    
    def get_tag(self, instance):
        tags = instance.tag.all()
        return [tag.name for tag in tags]
    
    class Meta:
        model = Post
        fields = '__all__'
        read_only_fields=[
            "id",
            "comments",
            "like_count"
        ]

class PostListSerializer(serializers.ModelSerializer):
    comments_cnt = serializers.SerializerMethodField()
    tag = serializers.SerializerMethodField()
    
    def get_comments_cnt(self, instance):
        return instance.comments.count()
    
    def get_tag(self, instance):
        tags = instance.tag.all()
        return [tag.name for tag in tags]
    
    class Meta:
        model=Post
        fields = [
            "id",
            "title",
            "writer",
            "image",
            "like_count",
            "comments_cnt",
            "tag"
        ]
        read_only_fields = ["id", "like_count", "comments_cnt"]

class CommentSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ['post']

class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'