from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.urls import reverse

from nests.models import Nest

from .models import Title, Unit, Topic, VideoContent, FileContent, ImageContent, TextContent, LinkContent


def _resolve_nest(nest_id):
    if not nest_id:
        return None
    return Nest.objects.filter(pk=nest_id, status=Nest.Status.APPROVED).first()


def _titles_url(nest=None):
    base_url = reverse("content:all_titles_view")
    if nest:
        return f"{base_url}?nest_id={nest.id}"
    return base_url


def _redirect_titles(nest=None):
    return redirect(_titles_url(nest))


def _require_auth(request: HttpRequest, message: str):
    messages.warning(request, message, "alert-warning")
    return redirect_to_login(request.get_full_path())


def _can_view_nest_content(user, nest: Nest):
    return nest.is_member(user) or nest.is_site_staff(user)


def _can_manage_nest_content(user, nest: Nest):
    return nest.is_nest_staff(user) or nest.is_site_staff(user)


def _enforce_view_permission(request: HttpRequest, nest: Nest | None):
    if not nest:
        return None

    if not request.user.is_authenticated:
        return _require_auth(request, "You must be signed in to view this nest content.")

    if not _can_view_nest_content(request.user, nest):
        messages.warning(request, "You must be an active member to view this nest content.", "alert-warning")
        return redirect("nests:nest_detail", nest_id=nest.id)

    return None


def _enforce_manage_permission(request: HttpRequest, nest: Nest | None):
    if nest:
        if not request.user.is_authenticated:
            return _require_auth(request, "You must be signed in to manage nest content.")

        if not _can_manage_nest_content(request.user, nest):
            messages.warning(request, "Only nest staff can manage this nest content.", "alert-warning")
            return redirect("nests:nest_detail", nest_id=nest.id)

        return None

    if not request.user.is_authenticated:
        return _require_auth(request, "You must be signed in to manage content.")

    if not request.user.is_staff:
        messages.warning(request, "Only staff can manage content", "alert-warning")
        return _redirect_titles()

    return None


# ==================== TITLE VIEWS ====================

def all_titles_view(request: HttpRequest):

    nest = _resolve_nest(request.GET.get("nest_id"))
    permission_response = _enforce_view_permission(request, nest)
    if permission_response:
        return permission_response
    titles = Title.objects.filter(nest=nest) if nest else Title.objects.all()

    return render(request, "content/all_titles.html", {"titles": titles, "nest": nest})


def title_detail_view(request: HttpRequest, title_id):

    try:
        title = Title.objects.get(pk=title_id)
        units = Unit.objects.filter(title=title)
    except Exception as e:
        print(e)
        return render(request, "404.html")

    permission_response = _enforce_view_permission(request, title.nest)
    if permission_response:
        return permission_response

    return render(request, "content/title_detail.html", {"title": title, "units": units, "nest": title.nest})


def create_title_view(request: HttpRequest):

    nest = _resolve_nest(request.GET.get("nest_id") or request.POST.get("nest_id"))
    permission_response = _enforce_manage_permission(request, nest)
    if permission_response:
        return permission_response

    if request.method == "POST":
        try:
            new_title = Title(
                name=request.POST["name"],
                description=request.POST.get("description", ""),
                sort_order=request.POST.get("sort_order", 0),
                is_published="is_published" in request.POST,
                created_by=request.user,
                nest=nest,
            )
            new_title.save()
            messages.success(request, "Title created successfully", "alert-success")
            return redirect("content:title_detail_view", title_id=new_title.id)
        except Exception as e:
            print(e)
            messages.error(request, "Couldn't create title", "alert-danger")

    return render(request, "content/create_title.html", {"nest": nest})


def update_title_view(request: HttpRequest, title_id):

    try:
        title = Title.objects.get(pk=title_id)
    except:
        return render(request, "404.html")

    permission_response = _enforce_manage_permission(request, title.nest)
    if permission_response:
        return permission_response

    if request.method == "POST":
        try:
            title.name = request.POST["name"]
            title.description = request.POST.get("description", "")
            title.sort_order = request.POST.get("sort_order", 0)
            title.is_published = "is_published" in request.POST
            title.save()
            messages.success(request, "Title updated successfully", "alert-success")
            return redirect("content:title_detail_view", title_id=title.id)
        except Exception as e:
            print(e)
            messages.error(request, "Couldn't update title", "alert-danger")

    return render(request, "content/update_title.html", {"title": title, "nest": title.nest})


def delete_title_view(request: HttpRequest, title_id):

    try:
        title = Title.objects.get(pk=title_id)
        nest = title.nest

        permission_response = _enforce_manage_permission(request, nest)
        if permission_response:
            return permission_response

        title.delete()
        messages.success(request, "Title deleted successfully", "alert-success")
        return _redirect_titles(nest)
    except Exception as e:
        print(e)
        messages.error(request, "Couldn't delete title", "alert-danger")

    return _redirect_titles()


# ==================== UNIT VIEWS ====================

def create_unit_view(request: HttpRequest, title_id):

    try:
        title = Title.objects.get(pk=title_id)
    except:
        return render(request, "404.html")

    permission_response = _enforce_manage_permission(request, title.nest)
    if permission_response:
        return permission_response

    if request.method == "POST":
        try:
            new_unit = Unit(
                title=title,
                name=request.POST["name"],
                description=request.POST.get("description", ""),
                sort_order=request.POST.get("sort_order", 0),
                is_published="is_published" in request.POST
            )
            new_unit.save()
            messages.success(request, "Unit created successfully", "alert-success")
            return redirect("content:title_detail_view", title_id=title.id)
        except Exception as e:
            print(e)
            messages.error(request, "Couldn't create unit", "alert-danger")

    return render(request, "content/create_unit.html", {"title": title, "nest": title.nest})


def unit_detail_view(request: HttpRequest, unit_id):

    try:
        unit = Unit.objects.get(pk=unit_id)
        topics = Topic.objects.filter(unit=unit)
    except Exception as e:
        print(e)
        return render(request, "404.html")

    permission_response = _enforce_view_permission(request, unit.title.nest)
    if permission_response:
        return permission_response

    return render(request, "content/unit_detail.html", {"unit": unit, "topics": topics, "nest": unit.title.nest})


def update_unit_view(request: HttpRequest, unit_id):

    try:
        unit = Unit.objects.get(pk=unit_id)
    except:
        return render(request, "404.html")

    permission_response = _enforce_manage_permission(request, unit.title.nest)
    if permission_response:
        return permission_response

    if request.method == "POST":
        try:
            unit.name = request.POST["name"]
            unit.description = request.POST.get("description", "")
            unit.sort_order = request.POST.get("sort_order", 0)
            unit.is_published = "is_published" in request.POST
            unit.save()
            messages.success(request, "Unit updated successfully", "alert-success")
            return redirect("content:unit_detail_view", unit_id=unit.id)
        except Exception as e:
            print(e)
            messages.error(request, "Couldn't update unit", "alert-danger")

    return render(request, "content/update_unit.html", {"unit": unit, "nest": unit.title.nest})


def delete_unit_view(request: HttpRequest, unit_id):

    nest = None

    try:
        unit = Unit.objects.get(pk=unit_id)
        title_id = unit.title.id
        nest = unit.title.nest

        permission_response = _enforce_manage_permission(request, nest)
        if permission_response:
            return permission_response

        unit.delete()
        messages.success(request, "Unit deleted successfully", "alert-success")
        return redirect("content:title_detail_view", title_id=title_id)
    except Exception as e:
        print(e)
        messages.error(request, "Couldn't delete unit", "alert-danger")

    return _redirect_titles(nest)


# ==================== TOPIC VIEWS ====================

def create_topic_view(request: HttpRequest, unit_id):

    try:
        unit = Unit.objects.get(pk=unit_id)
    except:
        return render(request, "404.html")

    permission_response = _enforce_manage_permission(request, unit.title.nest)
    if permission_response:
        return permission_response

    if request.method == "POST":
        try:
            new_topic = Topic(
                unit=unit,
                name=request.POST["name"],
                sort_order=request.POST.get("sort_order", 0),
                status=request.POST.get("status", "draft"),
                due_date=request.POST.get("due_date") or None
            )
            new_topic.save()
            messages.success(request, "Topic created successfully", "alert-success")
            return redirect("content:topic_detail_view", topic_id=new_topic.id)
        except Exception as e:
            print(e)
            messages.error(request, "Couldn't create topic", "alert-danger")

    return render(request, "content/create_topic.html", {"unit": unit, "status_choices": Topic.StatusChoices.choices, "nest": unit.title.nest})


def topic_detail_view(request: HttpRequest, topic_id):

    try:
        topic = Topic.objects.get(pk=topic_id)
        videos = VideoContent.objects.filter(topic=topic)
        files = FileContent.objects.filter(topic=topic)
        images = ImageContent.objects.filter(topic=topic)
        texts = TextContent.objects.filter(topic=topic)
        links = LinkContent.objects.filter(topic=topic)
    except Exception as e:
        print(e)
        return render(request, "404.html")

    permission_response = _enforce_view_permission(request, topic.unit.title.nest)
    if permission_response:
        return permission_response

    return render(request, "content/topic_detail.html", {
        "topic": topic,
        "videos": videos,
        "files": files,
        "images": images,
        "texts": texts,
        "links": links,
        "nest": topic.unit.title.nest,
    })


def update_topic_view(request: HttpRequest, topic_id):

    try:
        topic = Topic.objects.get(pk=topic_id)
    except:
        return render(request, "404.html")

    permission_response = _enforce_manage_permission(request, topic.unit.title.nest)
    if permission_response:
        return permission_response

    if request.method == "POST":
        try:
            topic.name = request.POST["name"]
            topic.sort_order = request.POST.get("sort_order", 0)
            topic.status = request.POST.get("status", "draft")
            topic.due_date = request.POST.get("due_date") or None
            topic.save()
            messages.success(request, "Topic updated successfully", "alert-success")
            return redirect("content:topic_detail_view", topic_id=topic.id)
        except Exception as e:
            print(e)
            messages.error(request, "Couldn't update topic", "alert-danger")

    return render(request, "content/update_topic.html", {"topic": topic, "status_choices": Topic.StatusChoices.choices, "nest": topic.unit.title.nest})


def delete_topic_view(request: HttpRequest, topic_id):

    nest = None

    try:
        topic = Topic.objects.get(pk=topic_id)
        unit_id = topic.unit.id
        nest = topic.unit.title.nest

        permission_response = _enforce_manage_permission(request, nest)
        if permission_response:
            return permission_response

        topic.delete()
        messages.success(request, "Topic deleted successfully", "alert-success")
        return redirect("content:unit_detail_view", unit_id=unit_id)
    except Exception as e:
        print(e)
        messages.error(request, "Couldn't delete topic", "alert-danger")

    return _redirect_titles(nest)


# ==================== VIDEO CONTENT ====================

def add_video_view(request: HttpRequest, topic_id):
    try:
        topic = Topic.objects.get(pk=topic_id)
    except:
        return render(request, "404.html")

    permission_response = _enforce_manage_permission(request, topic.unit.title.nest)
    if permission_response:
        return permission_response

    if request.method == "POST":
        try:
            new_video = VideoContent(
                topic=topic,
                video_title=request.POST["video_title"],
                video_file=request.FILES["video_file"],
                duration=request.POST.get("duration", 0),
                sort_order=request.POST.get("sort_order", 0)
            )
            if "thumbnail" in request.FILES:
                new_video.thumbnail = request.FILES["thumbnail"]
            new_video.save()
            messages.success(request, "Video added successfully", "alert-success")
        except Exception as e:
            print(e)
            messages.error(request, "Couldn't add video", "alert-danger")

    return redirect("content:topic_detail_view", topic_id=topic_id)


def delete_video_view(request: HttpRequest, video_id):
    try:
        video = VideoContent.objects.get(pk=video_id)
        topic_id = video.topic.id

        permission_response = _enforce_manage_permission(request, video.topic.unit.title.nest)
        if permission_response:
            return permission_response

        video.delete()
        messages.success(request, "Video deleted successfully", "alert-success")
        return redirect("content:topic_detail_view", topic_id=topic_id)
    except Exception as e:
        print(e)
        messages.error(request, "Couldn't delete video", "alert-danger")

    return _redirect_titles()


# ==================== FILE CONTENT ====================

def add_file_view(request: HttpRequest, topic_id):
    try:
        topic = Topic.objects.get(pk=topic_id)
    except:
        return render(request, "404.html")

    permission_response = _enforce_manage_permission(request, topic.unit.title.nest)
    if permission_response:
        return permission_response

    if request.method == "POST":
        try:
            uploaded_file = request.FILES["file"]
            file_type = uploaded_file.name.split(".")[-1] if "." in uploaded_file.name else ""
            display_name = request.POST.get("file_name") or uploaded_file.name

            new_file = FileContent(
                topic=topic,
                file_name=display_name,
                file=uploaded_file,
                file_type=file_type,
                sort_order=request.POST.get("sort_order", 0)
            )
            new_file.save()
            messages.success(request, "File added successfully", "alert-success")
        except Exception as e:
            print(e)
            messages.error(request, "Couldn't add file", "alert-danger")

    return redirect("content:topic_detail_view", topic_id=topic_id)


def delete_file_view(request: HttpRequest, file_id):
    try:
        file_obj = FileContent.objects.get(pk=file_id)
        topic_id = file_obj.topic.id

        permission_response = _enforce_manage_permission(request, file_obj.topic.unit.title.nest)
        if permission_response:
            return permission_response

        file_obj.delete()
        messages.success(request, "File deleted successfully", "alert-success")
        return redirect("content:topic_detail_view", topic_id=topic_id)
    except Exception as e:
        print(e)
        messages.error(request, "Couldn't delete file", "alert-danger")

    return _redirect_titles()


def download_file_view(request: HttpRequest, file_id):
    try:
        file_obj = FileContent.objects.get(pk=file_id)

        permission_response = _enforce_view_permission(request, file_obj.topic.unit.title.nest)
        if permission_response:
            return permission_response

        file_obj.download_count += 1
        file_obj.save()
    except Exception as e:
        print(e)
        messages.error(request, "File not found", "alert-danger")
        return _redirect_titles()

    return redirect(file_obj.file.url)


# ==================== IMAGE CONTENT ====================

def add_image_view(request: HttpRequest, topic_id):
    try:
        topic = Topic.objects.get(pk=topic_id)
    except:
        return render(request, "404.html")

    permission_response = _enforce_manage_permission(request, topic.unit.title.nest)
    if permission_response:
        return permission_response

    if request.method == "POST":
        try:
            new_image = ImageContent(
                topic=topic,
                image_title=request.POST.get("image_title", ""),
                image=request.FILES["image"],
                alt_text=request.POST.get("alt_text", ""),
                sort_order=request.POST.get("sort_order", 0)
            )
            new_image.save()
            messages.success(request, "Image added successfully", "alert-success")
        except Exception as e:
            print(e)
            messages.error(request, "Couldn't add image", "alert-danger")

    return redirect("content:topic_detail_view", topic_id=topic_id)


def delete_image_view(request: HttpRequest, image_id):
    try:
        image = ImageContent.objects.get(pk=image_id)
        topic_id = image.topic.id

        permission_response = _enforce_manage_permission(request, image.topic.unit.title.nest)
        if permission_response:
            return permission_response

        image.delete()
        messages.success(request, "Image deleted successfully", "alert-success")
        return redirect("content:topic_detail_view", topic_id=topic_id)
    except Exception as e:
        print(e)
        messages.error(request, "Couldn't delete image", "alert-danger")

    return _redirect_titles()


# ==================== TEXT CONTENT ====================

def add_text_view(request: HttpRequest, topic_id):
    try:
        topic = Topic.objects.get(pk=topic_id)
    except:
        return render(request, "404.html")

    permission_response = _enforce_manage_permission(request, topic.unit.title.nest)
    if permission_response:
        return permission_response

    if request.method == "POST":
        try:
            new_text = TextContent(
                topic=topic,
                text_title=request.POST.get("text_title", ""),
                body=request.POST["body"],
                format=request.POST.get("format", "plain"),
                sort_order=request.POST.get("sort_order", 0)
            )
            new_text.save()
            messages.success(request, "Text added successfully", "alert-success")
        except Exception as e:
            print(e)
            messages.error(request, "Couldn't add text", "alert-danger")

    return redirect("content:topic_detail_view", topic_id=topic_id)


def delete_text_view(request: HttpRequest, text_id):
    try:
        text = TextContent.objects.get(pk=text_id)
        topic_id = text.topic.id

        permission_response = _enforce_manage_permission(request, text.topic.unit.title.nest)
        if permission_response:
            return permission_response

        text.delete()
        messages.success(request, "Text deleted successfully", "alert-success")
        return redirect("content:topic_detail_view", topic_id=topic_id)
    except Exception as e:
        print(e)
        messages.error(request, "Couldn't delete text", "alert-danger")

    return _redirect_titles()


# ==================== LINK CONTENT ====================

def add_link_view(request: HttpRequest, topic_id):
    try:
        topic = Topic.objects.get(pk=topic_id)
    except:
        return render(request, "404.html")

    permission_response = _enforce_manage_permission(request, topic.unit.title.nest)
    if permission_response:
        return permission_response

    if request.method == "POST":
        try:
            new_link = LinkContent(
                topic=topic,
                display_text=request.POST["display_text"],
                url=request.POST["url"],
                sort_order=request.POST.get("sort_order", 0)
            )
            new_link.save()
            messages.success(request, "Link added successfully", "alert-success")
        except Exception as e:
            print(e)
            messages.error(request, "Couldn't add link", "alert-danger")

    return redirect("content:topic_detail_view", topic_id=topic_id)


def delete_link_view(request: HttpRequest, link_id):
    try:
        link = LinkContent.objects.get(pk=link_id)
        topic_id = link.topic.id

        permission_response = _enforce_manage_permission(request, link.topic.unit.title.nest)
        if permission_response:
            return permission_response

        link.delete()
        messages.success(request, "Link deleted successfully", "alert-success")
        return redirect("content:topic_detail_view", topic_id=topic_id)
    except Exception as e:
        print(e)
        messages.error(request, "Couldn't delete link", "alert-danger")

    return _redirect_titles()