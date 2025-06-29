# middleware.py
from django.shortcuts import redirect

class AccountValidationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                profile = request.user.userprofile
                if (profile.validation_requested and 
                    not profile.is_validated and 
                    not request.path.startswith(('/logout', '/pending-approval'))):
                    return redirect('pending_approval')
            except:
                pass
                
        return self.get_response(request)