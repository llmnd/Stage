from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .services import ChatbotService
from .models import ChatMessage

@login_required
def chat_view(request):
    # Récupérer l'historique des messages
    messages = ChatMessage.objects.filter(user=request.user).order_by('timestamp')[:20]
    return render(request, 'chatbot/chat.html', {'messages': messages})

@login_required
@require_POST
@csrf_exempt
def send_message(request):
    message = request.POST.get('message', '').strip()
    if not message:
        return JsonResponse({'error': 'Message vide'}, status=400)
    
    chatbot = ChatbotService()
    response = chatbot.process_message(request.user, message)
    
    return JsonResponse({
        'response': response,
        'status': 'success'
    })

@login_required
def get_messages(request):
    messages = ChatMessage.objects.filter(user=request.user).order_by('timestamp')[:20]
    messages_data = [{
        'message': msg.message,
        'is_user_message': msg.is_user_message,
        'timestamp': msg.timestamp.strftime("%d/%m/%Y %H:%M")
    } for msg in messages]
    
    return JsonResponse({'messages': messages_data})