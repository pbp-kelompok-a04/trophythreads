# forumApp/tests.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
import json
import uuid
from forumApp.models import ForumPost, Comment

# Mock Profile and its DoesNotExist exception for testing create_forum logic
class ProfileDoesNotExist(Exception): pass
class MockProfile:
    @staticmethod
    def objects():
        manager = MagicMock()
        # Default mock for user role
        manager.get.return_value = MagicMock(role='user')
        manager.DoesNotExist = ProfileDoesNotExist
        return manager
    DoesNotExist = ProfileDoesNotExist

class ForumAppTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_normal = User.objects.create_user(username='normal_user', password='testpassword')
        self.user_other = User.objects.create_user(username='other_user', password='testpassword')
        self.user_admin = User.objects.create_user(username='admin_user', password='testpassword')

        self.thread_personal = ForumPost.objects.create(
            title="Personal Thread", content="Content personal", author=self.user_normal
        )
        self.comment1 = Comment.objects.create(
            post=self.thread_personal, author=self.user_normal, content="Comment 1 content"
        )
        self.comment2 = Comment.objects.create(
            post=self.thread_personal, author=self.user_other, content="Comment 2 content"
        )
        
        # Patch the Profile model reference in views
        self.profile_patcher = patch('forumApp.views.Profile', new=MockProfile)
        self.profile_patcher.start()
        self.addCleanup(self.profile_patcher.stop)

    # --- LANDING PAGE/JSON VIEWS ---
    def test_show_landing_page_all_filters(self):
        ForumPost.objects.create(title="Official Post", content="", author=self.user_admin, post_type="official")
        
        # 'all' filter
        response_all = self.client.get(reverse('forumApp:show_landing_page'))
        self.assertEqual(len(response_all.context['forum_list']), 2)

        # 'personal' filter
        response_personal = self.client.get(reverse('forumApp:show_landing_page'), {'filter': 'personal'})
        self.assertEqual(len(response_personal.context['forum_list']), 1)

        # 'official' filter
        response_official = self.client.get(reverse('forumApp:show_landing_page'), {'filter': 'official'})
        self.assertEqual(len(response_official.context['forum_list']), 1)
        
        # Invalid filter defaults to all
        response_invalid = self.client.get(reverse('forumApp:show_landing_page'), {'filter': 'invalid'})
        self.assertEqual(len(response_invalid.context['forum_list']), 2)
        
    def test_show_json_logged_out_and_latest_post(self):
        response = self.client.get(reverse('forumApp:show_json'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check reverse order (comment2 is later than comment1)
        self.assertIn(self.comment2.author.username, data[0]['latest_post']) 
        
        # Logged out, is_author should be false
        self.assertFalse(data[0]['is_author'])

    def test_show_json_by_id_404(self):
        response_404 = self.client.get(reverse('forumApp:show_json_by_id', args=[uuid.uuid4()]))
        self.assertEqual(response_404.status_code, 404)
        
    # --- VIEWS/SESSION TESTS ---
    def test_increment_views_invalid_method(self):
        response = self.client.get(reverse('forumApp:increment_views', args=[self.thread_personal.id]))
        self.assertEqual(response.status_code, 405)

    def test_increment_views_same_session_no_increment(self):
        thread_id = str(self.thread_personal.id)
        
        # First POST increments
        self.client.post(reverse('forumApp:increment_views', args=[thread_id]))
        views_after_first = ForumPost.objects.get(pk=thread_id).views
        self.assertEqual(views_after_first, 1)
        
        # Second POST in same session returns 200 but doesn't increment DB
        response = self.client.post(reverse('forumApp:increment_views', args=[thread_id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ForumPost.objects.get(pk=thread_id).views, 1)
        self.assertIn('View already counted', response.json()['message'])
        
    # --- THREAD CRUD TESTS ---
    
    # create_forum
    def test_create_forum_invalid_method_and_json(self):
        self.client.force_login(self.user_normal)
        # Invalid Method
        response = self.client.get(reverse('forumApp:create_forum'))
        self.assertEqual(response.status_code, 405)
        # Invalid JSON
        response = self.client.post(reverse('forumApp:create_forum'), data="bad json", content_type='application/json')
        self.assertEqual(response.status_code, 400)
        
    def test_create_forum_admin_creates_official(self):
        # Configure mock for admin role
        with patch('forumApp.views.Profile.objects') as mock_manager:
            mock_manager.get.return_value = MagicMock(role='admin')
            self.client.force_login(self.user_admin)
            data = {"title": "Admin Post", "content": "Official content"}
            self.client.post(reverse('forumApp:create_forum'), data=json.dumps(data), content_type='application/json')
            self.assertEqual(ForumPost.objects.latest('created_at').post_type, 'official')

    # edit_thread
    def test_edit_thread_invalid_cases(self):
        self.client.force_login(self.user_normal)
        thread_id = str(self.thread_personal.id)
        data = {"title": "Updated", "content": "Updated"}
        
        # Invalid Method
        response = self.client.get(reverse('forumApp:edit_thread', args=[thread_id]))
        self.assertEqual(response.status_code, 405)
        
        # Invalid JSON
        response = self.client.post(reverse('forumApp:edit_thread', args=[thread_id]), data="bad json", content_type='application/json')
        self.assertEqual(response.status_code, 400)
        
        # Missing Content (Failure)
        response = self.client.post(reverse('forumApp:edit_thread', args=[thread_id]), data=json.dumps({"title": "X"}), content_type='application/json')
        self.assertEqual(response.status_code, 400)

        # Not author (Failure)
        self.client.force_login(self.user_other)
        response = self.client.post(reverse('forumApp:edit_thread', args=[thread_id]), data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 403)
        
    # delete_thread
    def test_delete_thread_invalid_method_and_auth(self):
        thread_id = str(self.thread_personal.id)
        
        # Invalid Method
        self.client.force_login(self.user_normal)
        response = self.client.get(reverse('forumApp:delete_thread', args=[thread_id]))
        self.assertEqual(response.status_code, 405)
        
        # Not author (Failure)
        self.client.force_login(self.user_other)
        response = self.client.delete(reverse('forumApp:delete_thread', args=[thread_id]))
        self.assertEqual(response.status_code, 403)
        
    # --- COMMENT CRUD TESTS ---
    
    # get_comments
    def test_get_comments_success_and_404(self):
        response = self.client.get(reverse('forumApp:get_comments', args=[self.thread_personal.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        
        # Check order (reversed by default in view)
        self.assertEqual(response.json()[0]['author'], self.user_other.username)

        response_404 = self.client.get(reverse('forumApp:get_comments', args=[uuid.uuid4()]))
        self.assertEqual(response_404.status_code, 404)

    # create_comment
    def test_create_comment_invalid_cases(self):
        self.client.force_login(self.user_normal)
        thread_id = str(self.thread_personal.id)
        
        # Invalid Method
        response = self.client.get(reverse('forumApp:create_comment', args=[thread_id]))
        self.assertEqual(response.status_code, 405)
        
        # Invalid JSON
        response = self.client.post(reverse('forumApp:create_comment', args=[thread_id]), data="bad json", content_type='application/json')
        self.assertEqual(response.status_code, 400)
        
        # Missing Content
        response = self.client.post(reverse('forumApp:create_comment', args=[thread_id]), data=json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        
    # edit_comment
    def test_edit_comment_invalid_cases(self):
        self.client.force_login(self.user_normal)
        comment_id = str(self.comment1.id)
        data = {"content": "Updated content"}
        
        # Invalid Method
        response = self.client.get(reverse('forumApp:edit_comment', args=[comment_id]))
        self.assertEqual(response.status_code, 405)

        # Not author (Failure)
        self.client.force_login(self.user_other)
        response = self.client.post(reverse('forumApp:edit_comment', args=[comment_id]), data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 403)
        
        # Success (Re-login as author)
        self.client.force_login(self.user_normal)
        response = self.client.post(reverse('forumApp:edit_comment', args=[comment_id]), data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # Comment not found
        response = self.client.post(reverse('forumApp:edit_comment', args=[uuid.uuid4()]), data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 404)

    # delete_comment
    def test_delete_comment_success_and_auth(self):
        comment_id = str(self.comment1.id)
        
        # 1. Not author (Failure)
        self.client.force_login(self.user_other)
        response = self.client.delete(reverse('forumApp:delete_comment', args=[comment_id]))
        self.assertEqual(response.status_code, 403)
        
        # 2. Success path
        self.client.force_login(self.user_normal)
        response = self.client.delete(reverse('forumApp:delete_comment', args=[comment_id]))
        self.assertEqual(response.status_code, 200)

        # 3. Comment not found
        response = self.client.delete(reverse('forumApp:delete_comment', args=[uuid.uuid4()]))
        self.assertEqual(response.status_code, 404)
        
    # --- MODEL TESTS (for coverage) ---
    def test_forum_post_model_str_and_increment(self):
        self.assertEqual(str(self.thread_personal), "Personal Thread")
        self.thread_personal.increment_views()
        self.assertEqual(self.thread_personal.views, 1)
