from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
import uuid


def validate_file_extension(value):
    valid_extensions = [".py", ".js", ".css", ".html"]
    if not any(value.name.endswith(ext) for ext in valid_extensions):
        raise ValidationError(
            f'Unsupported file extension. Allowed extensions are: {", ".join(valid_extensions)}'
        )


class CodeFile(models.Model):
    FILE_TYPES = [
        ("python", "Python"),
        ("javascript", "JavaScript"),
        ("css", "CSS"),
        ("html", "HTML"),
    ]

    name = models.CharField(max_length=255)
    owner = models.ForeignKey(
        User, related_name="owned_files", on_delete=models.CASCADE
    )
    collaborators = models.ManyToManyField(
        User, related_name="collaborative_files", blank=True
    )
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.file_type == "python" and not self.name.endswith(".py"):
            raise ValidationError("Python files must have a .py extension.")
        elif self.file_type == "javascript" and not self.name.endswith(".js"):
            raise ValidationError("JavaScript files must have a .js extension.")
        elif self.file_type == "css" and not self.name.endswith(".css"):
            raise ValidationError("CSS files must have a .css extension.")
        elif self.file_type == "html" and not self.name.endswith(".html"):
            raise ValidationError("HTML files must have a .html extension.")

    def is_collaborator(self, user):
        return user in self.collaborators.all()

    class Meta:
        unique_together = ("name", "owner")


class FileShareToken(models.Model):
    file = models.ForeignKey(
        CodeFile, related_name="share_tokens", on_delete=models.CASCADE
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ShareToken for {self.file.name}"
