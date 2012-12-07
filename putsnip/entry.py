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

def ready_context (request, current={}, post=False):
    current.update({
        'ac':request.session.get('ac', ''),
        'tags':tags
    })
    if post:
        current.update(csrf(request))
    return current

def ready_snips (snips):
    for snip in snips:
        snip.update_text_numbers()
        snip.get_tags_str()
        snip.get_key()
    return snips

def snippet(request, key):
    try:
        snip = models.Snip.get_snip(key)
    except Exception:
        return HttpResponse('Snip does not exist.')

    snip.add_view()
    snip.get_tags_str()
    snip.get_points()

    return render_to_response('snippet.html',
        ready_context(request, {'snip':snip}))

def unique(seq):
    seen = set()
    seen_add = seen.add
    return [ x for x in seq if x not in seen and not seen_add(x)]

def add(request):
    if not request.session.get('ac', False):
        return HttpResponseRedirect('/login?error=requires account, register or login')

    if request.method == 'POST':
        snip = models.Snip()

        if not len(request.POST['snip']):
            return render_to_response('add.html', ready_context(request, {'nocode':'1'}, True))

        # replace strange character I was getting an error with
        snip.code = request.POST['snip'].replace(u'\u200b', ' ')
        snip.desc = request.POST['desc'].replace(u'\u200b', ' ')

        snip.title = request.POST['title']
        if not len(snip.title):
            snip.title = 'Untitled'

        if not len(request.POST['lan']):
            request.POST['lan'] = 'plain'
        snip.lan = request.POST['lan'].replace(' ', '').lower()

        account = request.session.get('ac')
        snip.usr = account.usr

        snip.save()

        snip.vote(usr=account.id)

        # add tags & connections
        tags = [snip.lan]
        if len(request.POST['tags']) > 0:
            tags.extend(request.POST['tags'].lower().split(','))
        models.Tag.add_tags(snip.id, tags)

        return HttpResponseRedirect('/s/' + snip.get_key())

    return render_to_response('add.html', ready_context(request, post=True))

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
        c['snips'] = models.Snip.get_snip_by_tags(tags=['plain', 'test'], all=True)[0:50]
        c.update({'tag':key})

#    sort = sortkey[request.GET.get('sort', 'points')]
#    order = request.GET.get('order', 'desc')
#    c.update({sort:'1', order:'1'})
#
#    c['snips'] = c['snips'].order_by(sort)
#    if order == 'desc':
#        c['snips'] = c['snips'].reverse()[0:50]
#    else:
#        c['snips'] = c['snips'][0:50]

    ready_snips(c['snips'])

    return render_to_response('filter.html', ready_context(request, c))

def index(request):
    c = {'snips': ready_snips(models.Snip.super_filter()[0:10])}
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