from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from django.utils.timezone import is_naive, make_aware, utc

import jwt
from calendar import timegm
from datetime import timedelta, datetime


from pprint import PrettyPrinter
pprint = PrettyPrinter(indent=4).pprint



def make_utc(dt):
    if settings.USE_TZ and is_naive(dt):
        return make_aware(dt, timezone=utc)

    return dt

def aware_utcnow():
    return make_utc(datetime.utcnow())

def datetime_to_epoch(dt):
    return timegm(dt.utctimetuple())



def index(request):


    if request.user.is_authenticated:

        lifetime = timedelta(days=1)
        payload = {}
        payload['exp'] = datetime_to_epoch(aware_utcnow() + lifetime)
        payload['sub'] = request.user.username
        payload['aud'] = "Convergence"
        payload['displayName'] = request.user.username
        payload['firstName'] = request.user.first_name
        payload['lastName'] = request.user.last_name

        access_token = jwt.encode(payload, key=settings.JWT_RS256_SIGNING_KEY, algorithm='RS256', headers={'kid': "Django collab App"}).decode('utf-8')
    else:
        access_token = None

    context = {
        'access_token': access_token,
    }


    return render(request, 'collab/index.html', context)
