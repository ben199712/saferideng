from django.shortcuts import render


def home(request):
    return render(request, "home.html")


def static_test(request):
    return render(request, "static_test.html")


