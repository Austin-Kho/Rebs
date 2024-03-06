from django.db import transaction
from rest_framework import serializers

from work.models import (IssueProject, Role, Permission, Member, Membership, Module, Version,
                         IssueCategory, Repository, Tracker, IssueStatus, Workflow, CodeActivity,
                         CodeIssuePriority, CodeDocsCategory, Issue, IssueFile, IssueComment, TimeEntry)


# Work --------------------------------------------------------------------------
class FamilyTreeSerializer(serializers.ModelSerializer):
    """ recursive get patents -> for bread crumb """

    class Meta:
        model = IssueProject
        fields = ('pk', 'name', 'slug')


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ('pk', 'name', 'assignable', 'issue_visible', 'time_entry_visible',
                  'user_visible', 'order', 'user', 'created', 'updated')


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ('pk', 'project_create', 'project_update', 'project_close', 'project_delete',
                  'project_public', 'project_module', 'project_member', 'project_version',
                  'project_create_sub', 'project_pub_query', 'project_save_query',
                  'forum_read', 'forum_create', 'forum_update', 'forum_own_update',
                  'forum_delete', 'forum_own_delete', 'forum_watcher_read',
                  'forum_watcher_create', 'forum_watcher_delete', 'forum_manage',
                  'calendar_read',
                  'document_read', 'document_create', 'document_update', 'document_delete',
                  'file_read', 'file_manage',
                  'gantt_read',
                  'issue_read', 'issue_create', 'issue_update', 'issue_own_update', 'issue_copy',
                  'issue_rel_manage', 'issue_sub_manage', 'issue_public', 'issue_own_public',
                  'issue_comment_create', 'issue_comment_update', 'issue_comment_own_update',
                  'issue_private_comment_read', 'issue_private_comment_set', 'issue_delete',
                  'issue_watcher_read', 'issue_watcher_create', 'issue_watcher_delete', 'issue_import',
                  'issue_category_manage',
                  'news_read', 'news_manage', 'news_manage', 'news_comment',
                  'repo_changesets_read', 'repo_read', 'repo_commit_access', 'repo_rel_issue_manage', 'repo_manage',
                  'time_read', 'time_create', 'time_update', 'time_own_update',
                  'time_pro_act_manage', 'time_other_user_log', 'time_entries_import',
                  'wiki_read', 'wiki_history_read', 'wiki_page_export', 'wiki_page_update',
                  'wiki_page_rename', 'wiki_page_delete', 'wiki_attachment_delete', 'wiki_watcher_read',
                  'wiki_watcher_create', 'wiki_watcher_delete', 'wiki_page_project', 'wiki_manage')


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ('pk', 'user', 'roles')


class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = ('pk', 'project', 'member', 'role')


class TrackerInIssueProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tracker
        fields = ('pk', 'name', 'description')


class ModuleInIssueProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ('pk', 'project', 'issue', 'time', 'news', 'document',
                  'file', 'wiki', 'repository', 'forum', 'calendar', 'gantt')


class IssueProjectSerializer(serializers.ModelSerializer):
    family_tree = FamilyTreeSerializer(many=True, read_only=True)
    members = MemberSerializer(many=True, read_only=True)
    sub_projects = serializers.SerializerMethodField()
    trackers = TrackerInIssueProjectSerializer(many=True, read_only=True)
    user = serializers.SlugRelatedField('username', read_only=True)
    module = ModuleInIssueProjectSerializer(read_only=True)

    class Meta:
        model = IssueProject
        fields = ('pk', 'company', 'name', 'description', 'homepage', 'is_public',
                  'family_tree', 'parent', 'slug', 'status', 'is_inherit_members',
                  'depth', 'members', 'sub_projects', 'trackers', 'module', 'user', 'created')

    def get_sub_projects(self, obj):
        return self.__class__(obj.issueproject_set.all(), many=True, read_only=True).data

    @transaction.atomic
    def create(self, validated_data):
        parent = validated_data.get('parent', None)
        validated_data['depth'] = 1 if parent is None else parent.depth + 1
        project = IssueProject.objects.create(**validated_data)
        project.save()

        issue = self.initial_data.get('issue', True)
        time = self.initial_data.get('time', True)
        news = self.initial_data.get('news', True)
        document = self.initial_data.get('document', True)
        file = self.initial_data.get('file', True)
        wiki = self.initial_data.get('wiki', True)
        repository = self.initial_data.get('repository', False)
        forum = self.initial_data.get('forum', True)
        calendar = self.initial_data.get('calendar', True)
        gantt = self.initial_data.get('gantt', True)

        Module(project=project,
               issue=issue,
               time=time,
               news=news,
               document=document,
               file=file,
               wiki=wiki,
               repository=repository,
               forum=forum,
               calendar=calendar,
               gantt=gantt).save()

        return project

    @transaction.atomic
    def update(self, instance, validated_data):
        parent = validated_data.get('parent', None)
        instance.depth = 1 if parent is None else parent.depth + 1

        issue = self.initial_data.get('issue', True)
        time = self.initial_data.get('time', True)
        news = self.initial_data.get('news', True)
        document = self.initial_data.get('document', True)
        file = self.initial_data.get('file', True)
        wiki = self.initial_data.get('wiki', True)
        repository = self.initial_data.get('repository', False)
        forum = self.initial_data.get('forum', True)
        calendar = self.initial_data.get('calendar', True)
        gantt = self.initial_data.get('gantt', True)

        module = instance.module
        module.issue = issue
        module.time = time
        module.news = news
        module.document = document
        module.file = file
        module.wiki = wiki
        module.repository = repository
        module.forum = forum
        module.calendar = calendar
        module.gantt = gantt
        module.save()

        return super().update(instance, validated_data)


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ('pk', 'project', 'issue', 'time', 'news', 'document',
                  'file', 'wiki', 'repository', 'forum', 'calendar', 'gantt')


class VersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Version
        fields = ('pk', 'project', 'name', 'description', 'status',
                  'wiki_page_title', 'effective_date', 'share', 'is_default')


class RepositorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Repository
        fields = ('pk', 'project', 'scm', 'is_default',
                  'slug', 'path', 'path_encoding', 'is_report')


class TrackerSerializer(serializers.ModelSerializer):
    projects = FamilyTreeSerializer(many=True, read_only=True)

    class Meta:
        model = Tracker
        fields = ('pk', 'name', 'description', 'is_in_roadmap', 'default_status',
                  'projects', 'order', 'user', 'created', 'updated')


class IssueStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueStatus
        fields = ('pk', 'name', 'description', 'closed', 'order', 'user', 'created', 'updated')


class WorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        fields = ('pk', 'role', 'tracker', 'old_status', 'new_statuses')


class CodeActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeActivity
        fields = ('pk', 'name', 'active', 'default', 'order', 'user', 'created', 'updated')


class CodeIssuePrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeIssuePriority
        fields = ('pk', 'name', 'active', 'default', 'order', 'user', 'created', 'updated')


class CodeDocsCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeDocsCategory
        fields = ('pk', 'name', 'active', 'default', 'order', 'user', 'created', 'updated')


class IssueCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueCategory
        fields = ('pk', 'project', 'name', 'assigned_to')


class IssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = ('pk', 'project', 'tracker', 'is_private', 'subject', 'description',
                  'parent', 'status', 'priority', 'assigned_to', 'category', 'fixed_version',
                  'start_date', 'due_date', 'estimated_hours', 'done_ratio', 'watchers',
                  'closed', 'user', 'created', 'updated')


class IssueFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueFile
        fields = ('pk', 'issue', 'file', 'description')


class IssueCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueComment
        fields = ('pk', 'content', 'parent', 'user', 'created', 'updated')


class TimeEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeEntry
        fields = ('pk', 'issue', 'spent_on', 'hours', 'comment', 'activity', 'user', 'created', 'updated')
