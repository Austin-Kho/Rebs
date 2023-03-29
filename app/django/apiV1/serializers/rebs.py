from rest_framework import serializers

from rebs.models import (AccountSort, AccountSubD1, AccountSubD2, AccountSubD3,
                         ProjectAccountD1, ProjectAccountD2, CalendarSchedule, WiseSaying)


# Rebs --------------------------------------------------------------------------
class AccountSortSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountSort
        fields = ('pk', 'name')


class AccountSubD1Serializer(serializers.ModelSerializer):
    class Meta:
        model = AccountSubD1
        fields = ('pk', 'sorts', 'code', 'name', 'description')


class AccountSubD2Serializer(serializers.ModelSerializer):
    class Meta:
        model = AccountSubD2
        fields = ('pk', 'd1', 'code', 'name', 'description')


class AccountSubD3Serializer(serializers.ModelSerializer):
    class Meta:
        model = AccountSubD3
        fields = ('pk', 'd2', 'code', 'name', 'description', 'is_hide', 'is_special')


class ProjectAccountD1Serializer(serializers.ModelSerializer):
    sort_desc = serializers.CharField(source='get_sort_display', read_only=True)
    acc = serializers.SlugRelatedField(queryset=AccountSubD1.objects.all(), slug_field='name')

    class Meta:
        model = ProjectAccountD1
        fields = ('pk', 'sort_desc', 'acc', 'code', 'name', 'description')


class ProjectAccountD2Serializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectAccountD2
        fields = ('pk', 'd1', 'code', 'sub_title', 'name', 'description')


class CalendarScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarSchedule
        fields = ('pk', 'title', 'all_day', 'start_date', 'end_date', 'start_time', 'end_time')


class WiseSaySerializer(serializers.ModelSerializer):
    class Meta:
        model = WiseSaying
        fields = ('pk', 'saying_ko', 'saying_en', 'spoked_by')
