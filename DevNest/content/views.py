from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.contrib import messages

from .models import Title, Unit, Topic, VideoContent, FileContent, ImageContent, TextContent, LinkContent


# ==================== TITLE VIEWS ====================

def all_titles_view(request: HttpRequest):

    titles = Title.objects.all()

    return render(request, "content/all_titles.html", {"titles": titles})


def title_detail_view(request: HttpRequest, title_id):

    try:
        title = Title.objects.get(pk=title_id)
        units = Unit.objects.filter(title=title)
    except Exception as e:
        print(e)
        return render(request, "404.html")

    return render(request, "content/title_detail.html", {"title": title, "units": units})


def create_title_view(request: HttpRequest):

    if not request.user.is_authenticated:
        messages.warning(request, "You must be logged in", "alert-warning")
        return redirect("accounts:sign_in")

    if not request.user.is_staff:
        messages.warning(request, "Only staff can create titles", "alert-warning")
        return redirect("content:all_titles_view")

    if request.method == "POST":
        try:
            new_title = Title(
                name=request.POST["name"],
                description=request.POST.get("description", ""),
                sort_order=request.POST.get("sort_order", 0),
                is_published="is_published" in request.POST,
                created_by=request.user
            )
            new_title.save()
            messages.success(request, "Title created successfully", "alert-success")
            return redirect("content:title_detail_view", title_id=new_title.id)
        except Exception as e:
            print(e)
            messages.error(request, "Couldn't create title", "alert-danger")

    return render(request, "content/create_title.html")


def update_title_view(request: HttpRequest, title_id):

    if not request.user.is_authenticated:
        messages.warning(request, "You must be logged in", "alert-warning")
        return redirect("accounts:sign_in")

    if not request.user.is_staff:
        messages.warning(request, "Only staff can update titles", "alert-warning")
        return redirect("content:all_titles_view")

    try:
        title = Title.objects.get(pk=title_id)
    except:
        return render(request, "404.html")

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

    return render(request, "content/update_title.html", {"title": title})


def delete_title_view(request: HttpRequest, title_id):

    if not request.user.is_authenticated:
        messages.warning(request, "You must be logged in", "alert-warning")
        return redirect("accounts:sign_in")

    if not request.user.is_staff:
        messages.warning(request, "Only staff can delete titles", "alert-warning")
        return redirect("content:all_titles_view")

    try:
        title = Title.objects.get(pk=title_id)
        title.delete()
        messages.success(request, "Title deleted successfully", "alert-success")
    except Exception as e:
        print(e)
        messages.error(request, "Couldn't delete title", "alert-danger")

    return redirect("content:all_titles_view")


# ==================== UNIT VIEWS ====================

def create_unit_view(request: HttpRequest, title_id):

    if not request.user.is_authenticated:
        messages.warning(request, "You must be logged in", "alert-warning")
        return redirect("accounts:sign_in")

    if not request.user.is_staff:
        messages.warning(request, "Only staff can create units", "alert-warning")
        return redirect("content:all_titles_view")

    try:
        title = Title.objects.get(pk=title_id)
    except:
        return render(request, "404.html")

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

    return render(request, "content/create_unit.html", {"title": title})


def unit_detail_view(request: HttpRequest, unit_id):

    try:
        unit = Unit.objects.get(pk=unit_id)
        topics = Topic.objects.filter(unit=unit)
    except Exception as e:
        print(e)
        return render(request, "404.html")

    return render(request, "content/unit_detail.html", {"unit": unit, "topics": topics})


def update_unit_view(request: HttpRequest, unit_id):

    if not request.user.is_authenticated:
        messages.warning(request, "You must be logged in", "alert-warning")
        return redirect("accounts:sign_in")

    if not request.user.is_staff:
        messages.warning(request, "Only staff can update units", "alert-warning")
        return redirect("content:all_titles_view")

    try:
        unit = Unit.objects.get(pk=unit_id)
    except:
        return render(request, "404.html")

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

    return render(request, "content/update_unit.html", {"unit": unit})


def delete_unit_view(request: HttpRequest, unit_id):

    if not request.user.is_authenticated:
        messages.warning(request, "You must be logged in", "alert-warning")
        return redirect("accounts:sign_in")

    if not request.user.is_staff:
        messages.warning(request, "Only staff can delete units", "alert-warning")
        return redirect("content:all_titles_view")

    try:
        unit = Unit.objects.get(pk=unit_id)
        title_id = unit.title.id
        unit.delete()
        messages.success(request, "Unit deleted successfully", "alert-success")
        return redirect("content:title_detail_view", title_id=title_id)
    except Exception as e:
        print(e)
        messages.error(request, "Couldn't delete unit", "alert-danger")

    return redirect("content:all_titles_view")


# ==================== TOPIC VIEWS ====================

def create_topic_view(request: HttpRequest, unit_id):

    if not request.user.is_authenticated:
        messages.warning(request, "You must be logged in", "alert-warning")
        return redirect("accounts:sign_in")

    if not request.user.is_staff:
        messages.warning(request, "Only staff can create topics", "alert-warning")
        return redirect("content:all_titles_view")

    try:
        unit = Unit.objects.get(pk=unit_id)
    except:
        return render(request, "404.html")

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

    return render(request, "content/create_topic.html", {"unit": unit, "status_choices": Topic.StatusChoices.choices})


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

    return render(request, "content/topic_detail.html", {
        "topic": topic,
        "videos": videos,
        "files": files,
        "images": images,
        "texts": texts,
        "links": links
    })


def update_topic_view(request: HttpRequest, topic_id):

    if not request.user.is_authenticated:
        messages.warning(request, "You must be logged in", "alert-warning")
        return redirect("accounts:sign_in")

    if not request.user.is_staff:
        messages.warning(request, "Only staff can update topics", "alert-warning")
        return redirect("content:all_titles_view")

    try:
        topic = Topic.objects.get(pk=topic_id)
    except:
        return render(request, "404.html")

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

    return render(request, "content/update_topic.html", {"topic": topic, "status_choices": Topic.StatusChoices.choices})


def delete_topic_view(request: HttpRequest, topic_id):

    if not request.user.is_authenticated:
        messages.warning(request, "You must be logged in", "alert-warning")
        return redirect("accounts:sign_in")

    if not request.user.is_staff:
        messages.warning(request, "Only staff can delete topics", "alert-warning")
        return redirect("content:all_titles_view")

    try:
        topic = Topic.objects.get(pk=topic_id)
        unit_id = topic.unit.id
        topic.delete()
        messages.success(request, "Topic deleted successfully", "alert-success")
        return redirect("content:unit_detail_view", unit_id=unit_id)
    except Exception as e:
        print(e)
        messages.error(request, "Couldn't delete topic", "alert-danger")

    return redirect("content:all_titles_view")


# ==================== VIDEO CONTENT ====================

def add_video_view(request: HttpRequest, topic_id):

    if not request.user.is_authenticated:
        messages.warning(request, "You must be logged in", "alert-warning")
        return redirect("accounts:sign_in")

    if not request.user.is_staff:
        messages.warning(request, "Only staff can add content", "alert-warning")
        return redirect("content:all_titles_view")

    try:
        topic = Topic.objects.get(pk=topic_id)
    except:
        return render(request, "404.html")

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

    if not request.user.is_authenticated:
        messages.warning(request, "You must be logged in", "alert-warning")
        return redirect("accounts:sign_in")

    if not request.user.is_staff:
        messages.warning(request, "Only staff can delete content", "alert-warning")
        return redirect("content:all_titles_view")

    try:
        video = VideoContent.objects.get(pk=video_id)
        topic_id = video.topic.id
        video.delete()
        messages.success(request, "Video deleted successfully", "alert-success")
        return redirect("content:topic_detail_view", topic_id=topic_id)
    except Exception as e:
        print(e)
        messages.error(request, "Couldn't delete video", "alert-danger")

    return redirect("content:all_titles_view")


# ==================== FILE CONTENT ====================

def add_file_view(request: HttpRequest, topic_id):

    if not request.user.is_authenticated:
        messages.warning(request, "You must be logged in", "alert-warning")
        return redirect("accounts:sign_in")

    if not request.user.is_staff:
        messages.warning(request, "Only staff can add content", "alert-warning")
        return redirect("content:all_titles_view")

    try:
        topic = Topic.objects.get(pk=topic_id)
    except:
        return render(request, "404.html")

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

    if not request.user.is_authenticated:
        messages.warning(request, "You must be logged in", "alert-warning")
        return redirect("accounts:sign_in")

    if not request.user.is_staff:
        messages.warning(request, "Only staff can delete content", "alert-warning")
        return redirect("content:all_titles_view")

    try:
        file_obj = FileContent.objects.get(pk=file_id)
        topic_id = file_obj.topic.id
        file_obj.delete()
        messages.success(request, "File deleted successfully", "alert-success")
        return redirect("content:topic_detail_view", topic_id=topic_id)
    except Exception as e:
        print(e)
        messages.error(request, "Couldn't delete file", "alert-danger")

    return redirect("content:all_titles_view")


def download_file_view(request: HttpRequest, file_id):

    if not request.user.is_authenticated:
        messages.warning(request, "You must be logged in to download", "alert-warning")
        return redirect("accounts:sign_in")

    try:
        file_obj = FileContent.objects.get(pk=file_id)
        file_obj.download_count += 1
        file_obj.save()
    except Exception as e:
        print(e)
        messages.error(request, "File not found", "alert-danger")
        return redirect("content:all_titles_view")

    return redirect(file_obj.file.url)


# ==================== IMAGE CONTENT ====================

def add_image_view(request: HttpRequest, topic_id):

    if not request.user.is_authenticated:
        messages.warning(request, "You must be logged in", "alert-warning")
        return redirect("accounts:sign_in")

    if not request.user.is_staff:
        messages.warning(request, "Only staff can add content", "alert-warning")
        return redirect("content:all_titles_view")

    try:
        topic = Topic.objects.get(pk=topic_id)
    except:
        return render(request, "404.html")

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

    if not request.user.is_authenticated:
        messages.warning(request, "You must be logged in", "alert-warning")
        return redirect("accounts:sign_in")

    if not request.user.is_staff:
        messages.warning(request, "Only staff can delete content", "alert-warning")
        return redirect("content:all_titles_view")

    try:
        image = ImageContent.objects.get(pk=image_id)
        topic_id = image.topic.id
        image.delete()
        messages.success(request, "Image deleted successfully", "alert-success")
        return redirect("content:topic_detail_view", topic_id=topic_id)
    except Exception as e:
        print(e)
        messages.error(request, "Couldn't delete image", "alert-danger")

    return redirect("content:all_titles_view")


# ==================== TEXT CONTENT ====================

def add_text_view(request: HttpRequest, topic_id):

    if not request.user.is_authenticated:
        messages.warning(request, "You must be logged in", "alert-warning")
        return redirect("accounts:sign_in")

    if not request.user.is_staff:
        messages.warning(request, "Only staff can add content", "alert-warning")
        return redirect("content:all_titles_view")

    try:
        topic = Topic.objects.get(pk=topic_id)
    except:
        return render(request, "404.html")

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

    if not request.user.is_authenticated:
        messages.warning(request, "You must be logged in", "alert-warning")
        return redirect("accounts:sign_in")

    if not request.user.is_staff:
        messages.warning(request, "Only staff can delete content", "alert-warning")
        return redirect("content:all_titles_view")

    try:
        text = TextContent.objects.get(pk=text_id)
        topic_id = text.topic.id
        text.delete()
        messages.success(request, "Text deleted successfully", "alert-success")
        return redirect("content:topic_detail_view", topic_id=topic_id)
    except Exception as e:
        print(e)
        messages.error(request, "Couldn't delete text", "alert-danger")

    return redirect("content:all_titles_view")


# ==================== LINK CONTENT ====================

def add_link_view(request: HttpRequest, topic_id):

    if not request.user.is_authenticated:
        messages.warning(request, "You must be logged in", "alert-warning")
        return redirect("accounts:sign_in")

    if not request.user.is_staff:
        messages.warning(request, "Only staff can add content", "alert-warning")
        return redirect("content:all_titles_view")

    try:
        topic = Topic.objects.get(pk=topic_id)
    except:
        return render(request, "404.html")

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

    if not request.user.is_authenticated:
        messages.warning(request, "You must be logged in", "alert-warning")
        return redirect("accounts:sign_in")

    if not request.user.is_staff:
        messages.warning(request, "Only staff can delete content", "alert-warning")
        return redirect("content:all_titles_view")

    try:
        link = LinkContent.objects.get(pk=link_id)
        topic_id = link.topic.id
        link.delete()
        messages.success(request, "Link deleted successfully", "alert-success")
        return redirect("content:topic_detail_view", topic_id=topic_id)
    except Exception as e:
        print(e)
        messages.error(request, "Couldn't delete link", "alert-danger")

    return redirect("content:all_titles_view")