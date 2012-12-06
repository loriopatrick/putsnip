import base
from hashlib import md5
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.db import IntegrityError
from putsnip import models

def reference (request, current):
    current.update({'ac':request.session.get('ac', '')})
    return current

def simpnum (num):
    temp = round(num / 1000000, 1)
    if temp >= 1:
        return '%iM' % temp
    temp = round(num / 1000, 1)
    if temp >= 1:
        return '%ik' % temp
    return '%i' % num

def view_snips (snips):
    for snip in snips:
        snip.pointsK = simpnum(snip.points)
        snip.viewsK = simpnum(snip.views)
        snip.key = base.encode(snip.id)
    return snips

def snippet(request, key):
    try:
        snip = models.Snip.objects.get(id=base.decode(key))
    except Exception:
        return HttpResponse('Didn\'t find the snippet.')

    snip.views += 1
    snip.save()

    return render_to_response('snippet.html', reference(request, {
        'snip':snip
    }))

def unique(seq):
    seen = set()
    seen_add = seen.add
    return [ x for x in seq if x not in seen and not seen_add(x)]

def add(request):
    if not request.session.get('ac', False):
        return HttpResponseRedirect('/login?error=requires account, register or login')

    c = csrf(request)

    if request.method == 'POST':
        snip = models.Snip()

        if not len(request.POST['snip']):
            c.update({'nocode':'1'})
            return render_to_response('add.html', reference(request, c))

        snip.code = str(request.POST['snip'].replace(u'\u200b', ' '))

        snip.title = request.POST['title']
        if not len(snip.title):
            snip.title = 'Untitled'

        if not len(request.POST['lan']):
            request.POST['lan'] = 'plain'

        snip.lan = request.POST['lan'].replace(' ', '').lower()

        if len(request.POST['tags']) > 0:
            snip.tags = ','.join(unique(('%s,%s' % (request.POST['lan'], request.POST['tags'])).lower().split(',')))
        else:
            snip.tags = request.POST['lan'].lower()


        snip.name = request.session.get('ac').usr

        snip.save()

        return HttpResponseRedirect('/s/' + base.encode(snip.id))

    return render_to_response('add.html', reference(request, c))

sortkey = {
    'points':'points',
    'views':'views',
    'date':'datetime'
}

def filter(request, filter, key):
    c = {'snips':None}



    if filter == 'u':
        c['snips'] = models.Snip.objects.filter(name__exact=key)
        c.update({'name':key})
    elif filter == 't':
        c['snips'] = models.Snip.objects.filter(tags__contains=key)
        c.update({'tag':key})

    sort = sortkey[request.GET.get('sort', 'points')]
    order = request.GET.get('order', 'desc')
    c.update({sort:'1', order:'1'})

    c['snips'] = c['snips'].order_by(sort)
    if order == 'desc':
        c['snips'] = c['snips'].reverse()[0:50]
    else:
        c['snips'] = c['snips'][0:50]

    view_snips(c['snips'])

    return render_to_response('filter.html', reference(request, c))

def index(request):
    c = {'snips': models.Snip.objects.all()}

    sort = sortkey[request.GET.get('sort', 'points')]
    order = request.GET.get('order', 'desc')
    c.update({sort:'1', order:'1'})

    c['snips'] = c['snips'].order_by(sort)
    if order == 'desc':
        c['snips'] = c['snips'].reverse()[0:50]
    else:
        c['snips'] = c['snips'][0:50]

    view_snips(c['snips'])

    return render_to_response('filter.html', reference(request, c))

def login(request):
    c = csrf(request)

    if request.GET.get('error', False):
        c.update({'error':request.GET['error']})

    if request.session['ac'] is not None:
        c.update({'error':'logged out'})
        request.session['ac'] = None

    if request.method == 'POST':
        def error (msg):
            c.update({'error':msg})
            return render_to_response('login.html', c)
        def success (ac):
            request.session['ac'] = ac
            return HttpResponseRedirect('/')
        t = request.POST['type']

        if t == 'create':
            ac = models.Account()

            ac.usr = request.POST['user']
            if not len(ac.usr):
                return error('create account error:<br/>username required')

            ac.pwd = request.POST['pass']
            if not len(ac.pwd) or not len(request.POST['pass_verify']):
                return error('create account error:<br/>password and verification required')
            if ac.pwd != request.POST['pass_verify']:
                return error('create account error:<br/>passwords don\'t match')

            ac.pwd = md5(ac.pwd).hexdigest()
            ac.email = request.POST['email']

            try:
                ac.save()
            except IntegrityError:
                return error('create account error:<br/>account with username already exists')

            return success(ac)
        elif t == 'login':
            if not len(request.POST['user']):
                return error('login error:<br/>username required')
            if not len(request.POST['pass']):
                return error('login error:<br/>password required')

            try:
                ac = models.Account.objects.get(usr=request.POST['user'],
                    pwd=md5(request.POST['pass']).hexdigest())
            except Exception:
                return error('login error:<br/>username/password combination not found')

            return success(ac)
        else:
            return error('WTF?!?!<br/>Are you trying something sneeky?')

    return render_to_response('login.html', c)