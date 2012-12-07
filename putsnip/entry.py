import base
import analyze

from hashlib import md5
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.db import IntegrityError
from putsnip import models

tags = [
        {'name':'plain','size':'24','color':'255'},
        {'name':'plain','size':'24','color':'255'},
        {'name':'plain','size':'24','color':'255'},
        {'name':'plain','size':'24','color':'255'}
]

def ready_context (request, current, post=False):
    current.update({
        'ac':request.session.get('ac', ''),
        'tags':tags
    })
    if post:
        current.update(csrf(request))
    return current

def view_snips (snips):
    for snip in snips:
        snip.add_text_numbers()
    return snips

def snippet(request, key):
    try:
        snip = models.Snip.get_snip(key)
    except Exception:
        return HttpResponse('Snip does not exist.')

    snip.add_view()
    snip.get_tags()

    return render_to_response('snippet.html',
        ready_context(request, {'snip':snip}))

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
            return render_to_response('add.html', ready_context(request, c))

        # replace strange character I was getting an error with
        snip.code = str(request.POST['snip'].replace(u'\u200b', ' '))

        snip.title = request.POST['title']
        if not len(snip.title):
            snip.title = 'Untitled'

        if not len(request.POST['lan']):
            request.POST['lan'] = 'plain'
        snip.lan = request.POST['lan'].replace(' ', '').lower()

        snip.name = request.session.get('ac').usr

        snip.save()

        # add tags & connections
        tags = [snip.lan]
        if len(request.POST['tags']) > 0:
            tags.extend(request.POST['tags'].lower().split(','))
        models.Tag.add_tags(snip.id, tags)

        return HttpResponseRedirect('/s/' + snip.get_key())

    return render_to_response('add.html', ready_context(request, c))

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

    return render_to_response('filter.html', ready_context(request, c))

def index(request):
    c = {'snips': analyze.get_trending_snips()[0:10]}
    c['snips'] = view_snips(c['snips'])
    print c['snips']
    return render_to_response('filter.html', ready_context(request, c))

def login(request):
    c = csrf(request)

    if request.GET.get('error', False):
        c.update({'error':request.GET['error']})

    if request.session.get('ac', None) is not None:
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