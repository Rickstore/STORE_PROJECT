from django.conf import settings

class CartPersistenceMiddleware:
    """
    Middleware pour s'assurer que le panier est conservé dans la session
    même après une reconnexion où le framework Django pourrait potentiellement 
    réinitialiser ou remplacer la session (ex: lors d'un login vers un nouveau compte).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        was_authenticated = request.user.is_authenticated
        
        # On sauvegarde l'état du panier en début de requête
        cart_data = request.session.get(settings.CART_SESSION_ID)

        # La vue est traitée (ex: login_view s'exécute potentiellement ici)
        response = self.get_response(request)

        is_authenticated_now = request.user.is_authenticated

        # Si le panier a été perdu pendant le traitement
        if cart_data and settings.CART_SESSION_ID not in request.session:
            # On ne restaure pas le panier si l'utilisateur vient explicitement de se déconnecter
            # (cad authentifié avant, mais non authentifié après la vue logout)
            user_just_logged_out = (was_authenticated and not is_authenticated_now)
            
            if not user_just_logged_out:
                request.session[settings.CART_SESSION_ID] = cart_data
                request.session.modified = True

        return response
