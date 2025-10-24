from django.urls import path
from forumApp.views import show_landing_page, show_json, show_json_by_id, create_forum, get_comments, create_comment, show_thread_detail, edit_thread, delete_thread, edit_comment, delete_comment, increment_views
app_name = 'forumApp'

urlpatterns = [
    path('', show_landing_page, name='show_landing_page'),
    path('json/', show_json, name="show_json"),
    path('json/<str:id>/', show_json_by_id, name="show_json_by_id"),    
    path('create/', create_forum, name='create_forum'),
    
    path('<str:thread_id>/comments/', get_comments, name='get_comments'),
    path('<str:thread_id>/comments/create/', create_comment, name='create_comment'),
    path('comment/edit/<str:comment_id>/', edit_comment, name='edit_comment'),
    path('comment/delete/<str:comment_id>/', delete_comment, name='delete_comment'),
    
    path('edit/<str:thread_id>/', edit_thread, name='edit_thread'),
    path('delete/<str:thread_id>/', delete_thread, name='delete_thread'),
    path('<str:thread_id>/', show_thread_detail, name='show_thread_detail'),  
    path('views/increment/<str:thread_id>/', increment_views, name='increment_views'),  
]
