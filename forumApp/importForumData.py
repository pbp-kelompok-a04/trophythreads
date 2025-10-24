import os
import sys
import django
import csv
import uuid
from pathlib import Path
from datetime import datetime
from django.conf import settings
from django.db import transaction

BASE_DIR = Path(__file__).resolve().parent.parent 
APP_DIR = Path(__file__).resolve().parent 

sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trophythreads.settings')

POSTS_CSV_FILE = APP_DIR / 'posts.csv' 
COMMENTS_CSV_FILE = APP_DIR / 'comments.csv'

try:
    django.setup()
except Exception as e:
    sys.exit(1)

try:
    from django.contrib.auth.models import User
    from forumApp.models import ForumPost, Comment 
except ImportError as e:
    sys.exit(1)


def import_posts_and_users():
    all_usernames = set()
    
    for filename in [POSTS_CSV_FILE, COMMENTS_CSV_FILE]:
        try:
            with open(filename, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    all_usernames.add(row['author_username'])
        except FileNotFoundError:
            sys.exit(1)
        except Exception as e:
            sys.exit(1)
        
    users_map = {}
    for username in all_usernames:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'password': settings.SECRET_KEY, 'is_staff': False, 'is_active': True}
        )
        users_map[username] = user
        if created:
            print(f"  Membuat pengguna: {username}")
    

    posts_map = {}
    post_objects_to_create = []

    try:
        with open(POSTS_CSV_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                author_obj = users_map.get(row['author_username'])
                
                if not author_obj:
                    continue
                    
                # Siapkan objek ForumPost
                post = ForumPost(
                    id=uuid.UUID(row['id']),
                    title=row['title'],
                    image=row['image'] if row['image'] != 'null' else None,
                    content=row['content'],
                    author=author_obj,
                    post_type=row['post_type'],
                    views=int(row['views']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']),
                )
                post_objects_to_create.append(post)
                posts_map[str(post.id)] = post

        ForumPost.objects.bulk_create(post_objects_to_create, ignore_conflicts=True)

    except Exception as e:
        sys.exit(1)

    return posts_map, users_map

def import_comments(posts_map, users_map):
    comment_objects_to_create = []

    try:
        with open(COMMENTS_CSV_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                post_obj = posts_map.get(row['post_id'])
                author_obj = users_map.get(row['author_username'])

                if not post_obj:
                    continue
                if not author_obj:
                    continue

                comment = Comment(
                    id=uuid.UUID(row['id']),
                    post=post_obj,
                    author=author_obj,
                    content=row['content'],
                    image=row['image'] if row['image'] != 'null' else None,
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']),
                )
                comment_objects_to_create.append(comment)

        Comment.objects.bulk_create(comment_objects_to_create, ignore_conflicts=True)

    except Exception as e:
        sys.exit(1)

if __name__ == "__main__":
    posts, users = import_posts_and_users()
    import_comments(posts, users)
    print("Import dataset done")
