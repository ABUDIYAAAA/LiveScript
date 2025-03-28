from django.urls import path
from . import views

urlpatterns = [
    path("home/", views.home, name="home"),
    path("logout/", views.logout_view, name="logout"),
    path("create_file/", views.create_file, name="create_file"),
    path("rename_file/<int:file_id>/", views.rename_file, name="rename_file"),
    path("delete_file/<int:file_id>/", views.delete_file, name="delete_file"),
    path(
        "get_file_content/<int:file_id>/",
        views.get_file_content,
        name="get_file_content",
    ),
    path(
        "save_content/<int:file_id>/",
        views.save_content,  # Fix the view reference here
        name="save",
    ),
    path("share_file/<int:file_id>/", views.share_file, name="share_file"),
    path("access_file/<uuid:token>/", views.access_file, name="access_file"),
    path("run_code/<int:file_id>/", views.run_code, name="run_code"),
]
