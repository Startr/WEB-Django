from constance import config

def constance_config(request):
    """
    Add constance config to the template context.
    """
    return {'config': config}