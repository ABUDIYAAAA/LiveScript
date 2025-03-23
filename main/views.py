from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import CodeFile, FileShareToken
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied
from django.utils.timezone import now, timedelta
import subprocess
import tempfile
import sys  # Add this import
import os  # Add this import


@login_required
def home(request):
    if not request.user.is_active:
        return render(
            request, "main/home.html", {"message": "Please verify your email to start."}
        )

    owned_files = CodeFile.objects.filter(owner=request.user)
    collaborative_files = CodeFile.objects.filter(collaborators=request.user)
    return render(
        request,
        "main/home.html",
        {
            "username": request.user.username,
            "files": owned_files,
            "collaborative_files": collaborative_files,
        },
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
    file = get_object_or_404(CodeFile, id=file_id)

    # Ensure only the owner can delete
    if file.owner != request.user:
        raise PermissionDenied("You do not have permission to delete this file.")

    if request.method == "POST":
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

    # Ensure the user is either the owner or a collaborator
    if file.owner != request.user and request.user not in file.collaborators.all():
        return JsonResponse({"error": "Permission denied"}, status=403)

    # Force database refresh
    file.refresh_from_db()

    return JsonResponse({"success": True, "content": file.content})


@login_required
def save_content(request, file_id):
    file = get_object_or_404(CodeFile, id=file_id)

    # Ensure the user is either the owner or a collaborator
    if file.owner != request.user and request.user not in file.collaborators.all():
        raise PermissionDenied("You do not have permission to edit this file.")

    if request.method == "POST":
        new_content = request.POST.get("content")
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


@login_required
def share_file(request, file_id):
    file = get_object_or_404(CodeFile, id=file_id)

    # Ensure only the owner can generate a share token
    if file.owner != request.user:
        raise PermissionDenied("You do not have permission to share this file.")

    # Generate a new share token
    share_token = FileShareToken.objects.create(file=file)

    # Return the shareable link
    share_link = (
        f"{request.scheme}://{request.get_host()}/main/access_file/{share_token.token}/"
    )
    return JsonResponse({"success": True, "share_link": share_link})


def access_file(request, token):
    try:
        # Validate the token
        share_token = get_object_or_404(FileShareToken, token=token)

        # Add the user as a collaborator if they are authenticated
        if request.user.is_authenticated:
            file = share_token.file
            if (
                file.owner != request.user
                and request.user not in file.collaborators.all()
            ):
                file.collaborators.add(request.user)

        # Redirect to the home page (or file view if implemented)
        return redirect("home")
    except FileShareToken.DoesNotExist:
        return JsonResponse({"error": "Invalid or expired token."}, status=400)


@login_required
def run_code(request, file_id):
    file = get_object_or_404(CodeFile, id=file_id)

    # Ensure the user is either the owner or a collaborator
    if file.owner != request.user and request.user not in file.collaborators.all():
        raise PermissionDenied("You do not have permission to run this file.")
    if file.file_type != "py" and file.file_type != "python":
        return JsonResponse({"error": "Only Python files can be executed."}, status=400)

    if request.method == "POST":
        try:
            # Write the code to a temporary file
            with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
                temp_file.write(file.content.encode("utf-8"))
                temp_file_path = temp_file.name

            # Execute the Python file using the current Python interpreter
            result = subprocess.run(
                [sys.executable, temp_file_path],  # Use sys.executable
                capture_output=True,
                text=True,
                timeout=5,  # Limit execution time to 5 seconds
            )

            # Clean up the temporary file
            os.remove(temp_file_path)  # Use os.remove for cross-platform compatibility

            # Return the output or error
            if result.returncode == 0:
                return JsonResponse({"success": True, "output": result.stdout})
            else:
                return JsonResponse({"success": False, "error": result.stderr})
        except subprocess.TimeoutExpired:
            return JsonResponse({"error": "Code execution timed out."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)
