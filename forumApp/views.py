from django.shortcuts import render, redirect, get_object_or_404
from forumApp.models import ForumPost, Comment
from main.models import Profile
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from django.db.models import F 
import json

def show_landing_page(request):
    filter_type = request.GET.get("filter", "all")
    
    if filter_type == "all":
        forum_list = ForumPost.objects.all()
    if filter_type == "personal":
        forum_list = ForumPost.objects.filter(post_type="personal")
    elif filter_type == "official":
        forum_list = ForumPost.objects.filter(post_type="official")
    else:
        forum_list = ForumPost.objects.all()
        
    context = {
        "forum_list": forum_list,
        "filter_type": filter_type,
    }
    
    return render(request, "landingPage.html", context)

@csrf_exempt  
@login_required
def create_forum(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            title = data.get("title")
            content = data.get("content")
            image = data.get("image", None)

            if not title or not content:
                return JsonResponse({"error": "Title and content are required."}, status=400)

            user = request.user

            # Cek user dri profile class
            try:
                profile = Profile.objects.get(user=user)
                role = profile.role
            except Profile.DoesNotExist:
                role = "user"  

            if role in ["admin", "seller"]:
                post_type = "official"
            else:
                post_type = "personal"

            forum = ForumPost.objects.create(
                title=title,
                content=content,
                image=image,
                author=user,
                post_type=post_type,
                views=0, # Initial views count
            )

            return JsonResponse({
                "message": "Thread created successfully!",
                "thread": {
                    "id": str(forum.id),
                    "title": forum.title,
                    "content": forum.content,
                    "author": forum.author.username,
                    "post_type": forum.post_type,
                    "created_at": forum.created_at.isoformat() if forum.created_at else None
                }
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)

    return JsonResponse({"error": "Invalid request method."}, status=405)

# NEW: View to increment the views count via AJAX
@csrf_exempt
def increment_views(request, thread_id):
    if request.method == "POST":
        
        if not request.session.session_key:
            request.session.create()

        session_key = f'viewed_threads'
        viewed_threads = request.session.get(session_key, [])

        if thread_id in viewed_threads:
            return JsonResponse({'message': 'View already counted for this session.'}, status=200)
        
        try:
            forum_post = get_object_or_404(ForumPost, pk=thread_id)
            
            forum_post.views = F('views') + 1
            forum_post.save(update_fields=['views'])
            
            viewed_threads.append(thread_id)
            request.session[session_key] = viewed_threads
            request.session.modified = True
            
            forum_post.refresh_from_db()

            return JsonResponse({'message': 'View count incremented.', 'new_views': forum_post.views}, status=200)

        except ForumPost.DoesNotExist:
            return JsonResponse({"error": "Thread not found."}, status=404)
        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)


def show_json(request):
    user_id = request.user.id if request.user.is_authenticated else None
    forum_list = ForumPost.objects.all().prefetch_related('comments') 
    
    data = []
    for forum in forum_list:
        latest_comment = forum.comments.order_by('-created_at').first()
        comment_count = forum.comments.count()
        
        data.append({
            'id': str(forum.id),
            'title': forum.title,
            'image': forum.image,
            'content': forum.content,
            'author': forum.author.username,
            'author_id': forum.author.id,
            'post_type': forum.post_type,
            'views': forum.views, 
            'created_at': forum.created_at.isoformat() if forum.created_at else None,
            'updated_at': forum.updated_at.isoformat() if forum.updated_at else None,
            'is_author': forum.author.id == user_id, 
            'replies': comment_count,
            'latest_post': f"{latest_comment.author.username}: {latest_comment.content[:45]}" if latest_comment else None,
        })

    data.reverse()
    return JsonResponse(data, safe=False)

def show_json_by_id(request, id):
    user_id = request.user.id if request.user.is_authenticated else None
    try:
        forum = ForumPost.objects.select_related('author').get(pk=id)
        data = {
            'id': str(forum.id),
            'title': forum.title,
            'image': forum.image,
            'content': forum.content,
            'author': forum.author.username,
            'author_id': forum.author.id,
            'post_type': forum.post_type,
            'views': forum.views, 
            'created_at': forum.created_at.isoformat() if forum.created_at else None,
            'updated_at': forum.updated_at.isoformat() if forum.updated_at else None,
            'is_author': forum.author.id == user_id, 
        }
        return JsonResponse(data)
    except ForumPost.DoesNotExist:
        return JsonResponse({'detail': 'Not found'}, status=404)
    
def show_thread_detail(request, thread_id):
    context = {
        'thread_id': str(thread_id)
    }
    return render(request, "forumDetails.html", context)
    
def get_comments(request, thread_id):
    try:
        thread = ForumPost.objects.get(pk=thread_id)
        comments = Comment.objects.filter(post=thread).select_related('author').order_by('created_at')
        
        user_id = request.user.id if request.user.is_authenticated else None

        data = [
            {
                'id': str(comment.id),
                'content': comment.content,
                'image': comment.image,
                'author': comment.author.username,
                'created_at': comment.created_at.isoformat() if comment.created_at else None,
                'is_author': comment.author.id == user_id,
            }
            for comment in comments
        ]
        data.reverse()
        return JsonResponse(data, safe=False)
    except ForumPost.DoesNotExist:
        return JsonResponse({'error': 'Thread not found'}, status=404)
    
@csrf_exempt
@login_required
def create_comment(request, thread_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            content = data.get("content")
            image = data.get("image", None)

            if not content:
                return JsonResponse({"error": "Content is required."}, status=400)

            thread = ForumPost.objects.get(pk=thread_id)
            user = request.user

            comment = Comment.objects.create(
                post=thread,
                author=user,
                content=content,
                image=image,
            )

            return JsonResponse({
                "message": "Comment created successfully!",
                "comment": {
                    "id": str(comment.id),
                    "content": comment.content,
                    "image": comment.image,
                    "author": comment.author.username,
                    "created_at": comment.created_at.isoformat() if comment.created_at else None
                }
            }, status=201)

        except ForumPost.DoesNotExist:
            return JsonResponse({"error": "Thread not found."}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)

    return JsonResponse({"error": "Invalid request method."}, status=405)

@csrf_exempt  
@login_required
def edit_thread(request, thread_id):
    if request.method == "POST":
        try:
            forum_post = get_object_or_404(ForumPost, pk=thread_id)
            
            # Check only the author can edit
            if forum_post.author != request.user:
                return JsonResponse({"error": "You are not authorized to edit this thread."}, status=403)
                
            data = json.loads(request.body.decode("utf-8"))
            title = data.get("title")
            content = data.get("content")
            
            if not title or not content:
                return JsonResponse({"error": "Title and content are required."}, status=400)

            forum_post.title = title
            forum_post.content = content
            forum_post.save()

            return JsonResponse({
                "message": "Thread updated successfully!",
                "thread": {
                    "id": str(forum_post.id),
                    "title": forum_post.title,
                    "content": forum_post.content,
                }
            }, status=200)

        except ForumPost.DoesNotExist:
            return JsonResponse({"error": "Thread not found."}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)
    
    return JsonResponse({"error": "Invalid request method."}, status=405)

@csrf_exempt
@login_required
def delete_thread(request, thread_id):
    if request.method == "DELETE":
        try:
            forum_post = get_object_or_404(ForumPost, pk=thread_id)
            
            # Check only the author can delete
            if forum_post.author != request.user:
                return JsonResponse({"error": "You are not authorized to delete this thread."}, status=403)
                
            forum_post.delete()
            
            return JsonResponse({"message": "Thread deleted successfully!"}, status=200)

        except ForumPost.DoesNotExist:
            return JsonResponse({"error": "Thread not found."}, status=404)
        
    return JsonResponse({"error": "Invalid request method."}, status=405)

@csrf_exempt
@login_required
def edit_comment(request, comment_id):
    if request.method == "POST":
        try:
            comment = get_object_or_404(Comment, pk=comment_id)

            # Check only the author can edit
            if comment.author != request.user:
                return JsonResponse({"error": "You are not authorized to edit this comment."}, status=403)

            data = json.loads(request.body.decode("utf-8"))
            content = data.get("content")

            if not content:
                return JsonResponse({"error": "Content is required."}, status=400)

            comment.content = content
            comment.save()

            return JsonResponse({
                "message": "Comment updated successfully!",
                "comment": {
                    "id": str(comment.id),
                    "content": comment.content,
                }
            }, status=200)

        except Comment.DoesNotExist:
            return JsonResponse({"error": "Comment not found."}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)

    return JsonResponse({"error": "Invalid request method."}, status=405)


@csrf_exempt
@login_required
def delete_comment(request, comment_id):
    if request.method == "DELETE":
        try:
            comment = get_object_or_404(Comment, pk=comment_id)

            # Check only the author can delete
            if comment.author != request.user:
                return JsonResponse({"error": "You are not authorized to delete this comment."}, status=403)

            comment.delete()

            return JsonResponse({"message": "Comment deleted successfully!"}, status=200)

        except Comment.DoesNotExist:
            return JsonResponse({"error": "Comment not found."}, status=404)

    return JsonResponse({"error": "Invalid request method."}, status=405)
