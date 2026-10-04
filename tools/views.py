from django.shortcuts import render


def index(request):
    return render(request, "tools/index.html")


def walk_area(request):
    return render(request, "tools/walk_area.html")
