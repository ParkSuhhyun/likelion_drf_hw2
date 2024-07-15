from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny

from .models import *
from .serializers import *

from django.shortcuts import get_object_or_404

from .permissions import IsOwnerOrReadOnly
from rest_framework.exceptions import PermissionDenied

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    def get_serializer_class(self):
        if self.action == "list":
            return PostListSerializer
        return PostSerializer
    
    def get_permissions(self):
        if self.action in ["create"]:
            return [IsAuthenticated()]
        elif self.action in ["update", "destroy", "partial_update"]:
            return [IsOwnerOrReadOnly()]
        return [AllowAny()]
    
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        post = serializer.instance
        self.handle_tags(post)

        return Response(serializer.data)
    
    def perform_update(self, serializer):
        post = serializer.save()
        post.tag.clear()
        self.handle_tags(post)

    def handle_tags(self, post):
        tags = [word[1:] for word in post.content.split(' ') if word.startswith('#')]
        for t in tags:
            tag, created = Tag.objects.get_or_create(name=t)
            post.tag.add(tag)
        post.save()

    @action(methods=['GET'], detail=True)
    def likes(self, request, pk=None):
        like_post = self.get_object()
        if request.user in like_post.like.all():
            like_post.like.remove(request.user)
            like_post.like_count -= 1
        else:        
            like_post.like.add(request.user)
            like_post.like_count += 1
        like_post.save(update_fields=["like_count"])
        return Response()

    @action(methods=['GET'], detail=False)
    def top3(self, request):
        top_post = Post.objects.all().order_by('-like_count')[:3]
        serializer = PostSerializer(top_post, many=True)
        return Response(serializer.data)

# 댓글 디테일 조회, 수정, 삭제
class CommentViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def get_permissions(self):
        if self.action in ["update", "destroy", "partial_update"]:
            return [IsOwnerOrReadOnly()]
        return []
    
# 포스트 게시물에 있는 댓글 목록 조회, 포스트 게시물에 댓글 작성
class PostCommentViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        post = self.kwargs.get("post_id")
        queryset = Comment.objects.filter(post_id=post)
        return queryset
    
    def create(self, request, post_id=None):
        post = get_object_or_404(Post, id=post_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(post=post)
        return Response(serializer.data)
    
    def get_permissions(self):
        return [permission() for permission in self.permission_classes]
    
class TagViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    queryset=Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = "name"
    lookup_url_kwarg = "tag_name"

    def retrieve(self, request, *args, **kwargs):
        tag_name = kwargs.get("tag_name")
        tag = get_object_or_404(Tag, name=tag_name)
        posts = Post.objects.filter(tag=tag)
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)