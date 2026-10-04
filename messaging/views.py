from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from listings.models import Property
from .forms import MessageForm
from .models import Thread, Message


@login_required
def thread_list(request):
    threads = Thread.objects.filter(Q(buyer=request.user) | Q(seller=request.user)).order_by("-created_at")
    return render(request, "messaging/thread_list.html", {"threads": threads})


@login_required
def start_thread(request, property_id: int):
    prop = get_object_or_404(Property, pk=property_id, is_active=True)
    if prop.owner == request.user:
        return redirect("property_detail", pk=prop.pk)

    thread, _ = Thread.objects.get_or_create(property=prop, buyer=request.user, seller=prop.owner)
    return redirect("thread_detail", thread_id=thread.id)


@login_required
def thread_detail(request, thread_id: int):
    thread = get_object_or_404(Thread, id=thread_id)
    if request.user not in [thread.buyer, thread.seller]:
        return redirect("thread_list")

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            Message.objects.create(thread=thread, sender=request.user, body=form.cleaned_data["body"])
            return redirect("thread_detail", thread_id=thread.id)
    else:
        form = MessageForm()

    return render(request, "messaging/thread_detail.html", {"thread": thread, "form": form})
