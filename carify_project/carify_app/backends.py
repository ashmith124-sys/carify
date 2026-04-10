from allauth.account.auth_backends import AuthenticationBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class CaseSensitiveAuthBackend(AuthenticationBackend):
    """
    Extends the default Allauth AuthenticationBackend to strictly enforce
    case-sensitive usernames during login operations.
    If the user logs in via email, it remains case-insensitive (standard practice),
    but username inputs MUST match exactly.
    """
    def authenticate(self, request, **credentials):
        user = super().authenticate(request, **credentials)
        
        # If successfully authenticated by allauth, verify exact casing
        if user:
            login_field = credentials.get('username') or credentials.get('login')
            
            # If the user logged in using a username (not an email)
            if login_field and '@' not in login_field:
                if user.username != login_field:
                    # Reject authentication if case does not match exactly
                    return None
                    
        return user
