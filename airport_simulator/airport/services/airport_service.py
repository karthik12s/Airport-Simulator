from ..models import Airport

def get_all_airports():
    return Airport.objects.prefetch_related('terminals__airport_entity')