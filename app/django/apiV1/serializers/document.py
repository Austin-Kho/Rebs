import json
from django.db import transaction
from django.core.exceptions import ValidationError
from urllib.parse import urlsplit, urlunsplit
from rest_framework import serializers

from document.models import (Group, Board, Category, LawsuitCase, Post,
                             Like, DisLike, Image, Link, File, Comment, Tag)


# Document --------------------------------------------------------------------------
class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('pk', 'name', 'manager')


class BoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = ('pk', 'group', 'name', 'order', 'search_able', 'manager')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('pk', 'board', 'name', 'parent', 'order')


class LawSuitCaseSerializer(serializers.ModelSerializer):
    proj_name = serializers.SlugField(source='project', read_only=True)
    sort_desc = serializers.CharField(source='get_sort_display', read_only=True)
    level_desc = serializers.CharField(source='get_level_display', read_only=True)
    related_case_name = serializers.SlugField(source='related_case', read_only=True)
    court_desc = serializers.CharField(source='get_court_display', read_only=True)
    user = serializers.SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        model = LawsuitCase
        fields = ('pk', 'company', 'project', 'proj_name', 'sort', 'sort_desc', 'level',
                  'level_desc', 'related_case', 'related_case_name', 'court', 'court_desc',
                  'other_agency', 'case_number', 'case_name', 'plaintiff', 'defendant',
                  'related_debtor', 'case_start_date', 'summary', 'user', 'created')


class SimpleLawSuitCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = LawsuitCase
        fields = ('pk', '__str__')


class LinksInPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = ('pk', 'post', 'link', 'hit')


class FilesInPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ('pk', 'post', 'file', 'hit')


class PostSerializer(serializers.ModelSerializer):
    proj_name = serializers.SlugField(source='project', read_only=True)
    cate_name = serializers.SlugField(source='category', read_only=True)
    lawsuit_name = serializers.SlugField(source='lawsuit', read_only=True)
    links = LinksInPostSerializer(many=True, read_only=True)
    files = FilesInPostSerializer(many=True, read_only=True)
    comments = serializers.RelatedField(many=True, read_only=True)
    user = serializers.SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        model = Post
        fields = ('pk', 'company', 'project', 'proj_name', 'board', 'is_notice', 'category',
                  'cate_name', 'lawsuit', 'lawsuit_name', 'title', 'execution_date',
                  'is_hide_comment', 'content', 'hit', 'blame', 'ip', 'device', 'secret', 'password',
                  'links', 'files', 'comments', 'user', 'soft_delete', 'created', 'updated', 'is_new')
        read_only_fields = ('ip',)

    def to_python(self, value):

        def split_url(url):
            """
            Return a list of url parts via urlparse.urlsplit(), or raise
            ValidationError for some malformed URLs.
            """
            try:
                return list(urlsplit(url))
            except ValueError:
                # urlparse.urlsplit can raise a ValueError with some
                # misformatted URLs.
                raise ValidationError(self.error_messages['invalid'], code='invalid')

        if value:
            url_fields = split_url(value)
            if not url_fields[0]:
                # If no URL scheme given, assume http://
                url_fields[0] = 'http'
            if not url_fields[1]:
                # Assume that if no domain is provided, that the path segment
                # contains the domain.
                url_fields[1] = url_fields[2]
                url_fields[2] = ''
                # Rebuild the url_fields list, since the domain segment may now
                # contain the path too.
                url_fields = split_url(urlunsplit(url_fields))
            value = urlunsplit(url_fields)
        return value

    @transaction.atomic
    def create(self, validated_data):
        validated_data['ip'] = self.context.get('request').META.get('REMOTE_ADDR')
        post = Post.objects.create(**validated_data)

        # Links 처리
        new_links = self.initial_data.getlist('newLinks')
        if new_links:
            for link in new_links:
                Link.objects.create(post=post, link=self.to_python(link))

        # Files 처리
        new_files = self.initial_data.getlist('newFiles')
        if new_files:
            for file in new_files:
                File.objects.create(post=post, file=file)

        return post

    @transaction.atomic
    def update(self, instance, validated_data):
        validated_data['ip'] = self.context.get('request').META.get('REMOTE_ADDR')
        instance.__dict__.update(**validated_data)
        instance.category = validated_data.get('category', instance.category)
        instance.save()

        # Links 처리
        old_links = self.initial_data.getlist('links')
        if old_links:
            for json_link in old_links:
                link = json.loads(json_link)
                link_object = Link.objects.get(pk=link.get('pk'))
                if link.get('del'):
                    link_object.delete()
                else:
                    link_object.link = self.to_python(link.get('link'))
                    link_object.save()

        new_links = self.initial_data.getlist('newLinks')
        if new_links:
            for link in new_links:
                Link.objects.create(post=instance, link=self.to_python(link))

        # Files 처리
        old_files = self.initial_data.getlist('files')
        if old_files:
            cng_pks = self.initial_data.getlist('cngPks')
            cng_files = self.initial_data.getlist('cngFiles')
            cng_maps = [(pk, cng_files[i]) for i, pk in cng_pks]  # 아래 로직에서 파일 변경 로직 작성 요망
            for json_file in old_files:
                file = json.loads(json_file)
                pk = file.get('pk')
                file_object = File.objects.get(pk=pk)
                for m in cng_maps:
                    if pk in m:
                        file_object.file = m[1]
                        file_object.save()
                # nf = [nf.get('file') for nf in cng_files if nf.get('pk') == file.get('pk')]
                # if nf:
                #     file['newFile'] = nf[0]
                if file.get('del'):
                    file_object.delete()
                elif file.get('newFile'):
                    file_object.file = file.get('newFile')
                    file_object.save()

        new_files = self.initial_data.getlist('newFiles')
        if new_files:
            for file in new_files:
                File.objects.create(post=instance, file=file)

        return instance


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ('pk', 'user', 'post')


class DisLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisLike
        fields = ('pk', 'user', 'post')


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ('pk', 'post', 'image')


class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = ('pk', 'post', 'link', 'hit')


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ('pk', 'post', 'file', 'hit')


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = (
            'pk', 'post', 'content', 'like', 'dislike', 'blame', 'ip',
            'device', 'secret', 'password', 'soft_delete')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('pk', 'board', 'name', 'post')
