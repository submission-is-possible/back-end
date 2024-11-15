from django.contrib.sessions.models import Session
from django.http import JsonResponse
from users.models import User

def get_user(func):
    def wrapper(*args, **kwargs):
        if args:
            print(args)
            request = args[0]
            session_key = request.session

            if (session_key):
                session_data = Session.objects.get(session_key=session_key.session_key)

                user = User.objects.get(id=session_data.get_decoded().get('_auth_user_id'))
                if ( user ):
                    args[0].user = user
                else:
                   return JsonResponse({"error": "User Must be logged in"}, status=400) 
            else:
                return JsonResponse({"error": "User Must be logged in"}, status=400)
        # Call the original function with the modified arguments
        return func(*args, **kwargs)
    
    return wrapper