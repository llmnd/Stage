from django.shortcuts import render
def bonjour(request):
    return render(request, 'accueil/bonjour.html')
