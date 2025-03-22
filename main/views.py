from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import CodeFile
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied


@login_required
def home(request):
    if not request.user.is_active:
        return render(
            request, "main/home.html", {"message": "Please verify your email to start."}
        )

    files = CodeFile.objects.filter(owner=request.user)
    return render(
        request, "main/home.html", {"username": request.user.username, "files": files}
    )


@login_required
def create_file(request):
    if request.method == "POST":
        name = request.POST.get("name")
        file_type = request.POST.get("file_type")
        if name and file_type:
            file = CodeFile.objects.create(
                owner=request.user, name=name, file_type=file_type, content=""
            )
            return JsonResponse(
                {"id": file.id, "name": file.name, "file_type": file.file_type}
            )
    return JsonResponse({"error": "Invalid data"}, status=400)


@login_required
def rename_file(request, file_id):
    if request.method == "POST":
        file = get_object_or_404(CodeFile, id=file_id)

        # Ensure only the owner can rename
        if file.owner != request.user:
            raise PermissionDenied("You do not have permission to rename this file.")

        new_name = request.POST.get("new_name")
        if new_name:
            file.name = new_name
            file.save()
            return JsonResponse({"success": True, "new_name": new_name})
    return JsonResponse({"error": "Invalid data"}, status=400)


@login_required
def delete_file(request, file_id):
    if request.method == "POST":
        file = get_object_or_404(CodeFile, id=file_id)

        # Ensure only the owner can delete
        if file.owner != request.user:
            raise PermissionDenied("You do not have permission to delete this file.")

        confirm_name = request.POST.get("confirm_name")
        if confirm_name == file.name:
            file.delete()
            return JsonResponse({"success": True})
        return JsonResponse({"error": "File name does not match"}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def get_file_content(request, file_id):
    file = get_object_or_404(CodeFile, id=file_id)

    # Ensure only the owner can view content
    if file.owner != request.user:
        return JsonResponse({"error": "Permission denied"}, status=403)

    # Force database refresh
    file.refresh_from_db()

    return JsonResponse({"success": True, "content": file.content})


@login_required
def save_content(request, file_id):
    print("save_content")
    if request.method == "POST":
        file = get_object_or_404(CodeFile, id=file_id)

        # Ensure only the owner can save content
        if file.owner != request.user:
            raise PermissionDenied("You do not have permission to edit this file.")

        new_content = request.POST.get("content")
        print(new_content)
        if new_content is not None:
            file.content = new_content
            file.save()

            # Force a refresh from the database to ensure we're getting the latest data
            file.refresh_from_db()

            return JsonResponse(
                {
                    "success": True,
                    "message": "Content saved successfully.",
                    "content": file.content,  # Return the actual saved content
                }
            )
    return JsonResponse({"error": "Invalid request"}, status=400)
