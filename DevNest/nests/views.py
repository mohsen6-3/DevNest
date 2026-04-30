from django.http import HttpRequest
from django.shortcuts import redirect, redirect, render
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Nest


def nest_dashboard(request):
    nests = Nest.objects.filter(members=request.user)
    return render(request, "nests/dashboard.html", {
        "nests": nests
    })

# name = models.CharField(max_length=255)
# description = models.TextField()
# creator = models.ForeignKey(User, on_delete=models.CASCADE)
# members = models.ManyToManyField(User, related_name="nests")
# created_at = models.DateTimeField(auto_now_add=True)
def add_nest_view(request: HttpRequest):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        creator = request.user
        members_ids = request.POST.getlist('members')

        new_nest = Nest.objects.create(
            name=name,
            description=description,
            creator=creator,
        )
        new_nest.members.set(members_ids)
        return redirect('nests:nest_dashboard')


    users = User.objects.all()
    return render(request, 'nests/add_nest.html', {
        'users': users
    })
