from staff_control.models import StaffPermission


def staff_permissions(request):
    """Inject allowed_nav into all templates for staff users."""
    allowed_nav = []
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            if profile.role == 'staff':
                perm = StaffPermission.get_or_create_for_staff(request.user)
                allowed_nav = perm.allowed_nav
            elif profile.role == 'admin':
                from staff_control.models import ALL_FEATURE_KEYS
                allowed_nav = ALL_FEATURE_KEYS
        except Exception:
            pass
    return {'allowed_nav': allowed_nav}
