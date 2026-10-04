from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import UploadDocForm
from .models import Profile, VerificationDocument


@login_required
def dashboard(request):
    profile = Profile.objects.get(user=request.user)
    docs = VerificationDocument.objects.filter(user=request.user)
    return render(request, "verification/dashboard.html", {"profile": profile, "docs": docs})


@login_required
def upload_doc(request):
    if request.method == "POST":
        form = UploadDocForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.user = request.user
            doc.save()
            return redirect("verify_dashboard")
    else:
        form = UploadDocForm()
    return render(request, "verification/upload.html", {"form": form})
