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
]
