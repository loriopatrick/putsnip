from hashlib import md5
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.db import IntegrityError
from putsnip import models

import httplib
conn = httplib.HTTPConnection('putsnip.com')
conn.request('GET', 'index.html')


def ready_context(request, current={}, post=False):
    current.update({
        'ac': request.session.get('ac', None),
        'tags_trend': models.Tag.get_pop_tags()[:20]
    })
    if post:
        current.update(csrf(request))
    return current


def ready_snips(snips, ac=None):
    for snip in snips:
        snip.update_text_numbers()
        snip.get_tags_str()
        snip.get_key()
        if ac:
            snip.get_vote(usr=ac.id)
    return snips


def snippet(request, key):
    try:
        snip = models.Snip.get_snip(key)
    except Exception:
        return HttpResponse('Snip does not exist.')

    snip.add_view()
    snip.get_key()
    snip.get_tags_str()
    snip.get_points()
    ac = request.session.get('ac', None)
    if ac:
        snip.get_vote(usr=ac.id)

    return render_to_response('snippet.html',
        ready_context(request, {'snip': snip, 'title':snip.title}))


def unique(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if x not in seen and not seen_add(x)]


def add(request):
    if not request.session.get('ac', False):
        return HttpResponseRedirect('/login?error=requires account, register or login&redirect=/add')

    if request.method == 'POST':
        snip = models.Snip()

        if not len(request.POST['snip']):
            return render_to_response('add.html', ready_context(request, {'nocode': '1'}, True))

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
    'points': 'points',
    'views': 'views',
    'date': 'datetime'
}

def filter(request):
    c = {'snips': None}
    get = request.GET.get

    page = int(get('page', '0'))
    dir = get('dir', None)
    if dir == 'previous':
        page = max(page - 1, 0)
    elif dir == 'next':
        page += 1

    items = min(max(int(get('n', '50')), 5), 70)

    def split(tags):
        if tags is None or not len(tags):
            return None
        return tags.split(',')

    sort = {'hot': 'hot',
            'points': 'points',
            'views': 'views',
            'datetime': 'datetime'}[get('sort', 'hot')]

    order = {'d': 'DESC', 'a': 'ASC'}[get('or', 'd')]
    user = get('usr', '')

    c['snips'] = models.Snip.super_filter(
        tags=split(get('tags', None)),
        all_tags=get('at', 'n') == 'y',
        user=user,
        sort=sort,
        order=order
    )[items * page:items * (page + 1)]

    ready_snips(c['snips'], request.session.get('ac', None))

    c.update({
        'tags': get('tags', ''),
        'usr': user,
        sort: '1',
        order: '1',
        'page': page,
        'title': (get('tags', '') + ' ' + user)
    })

    if get('at', 'n') == 'y':
        c.update({'ht': '1'})
    else:
        c.update({'ct': '1'})

    return render_to_response('filter.html', ready_context(request, c))


def redirect(request, type, key):
    if type == 'uv' or type == 'dv':
        ac = request.session.get('ac', None)
        if ac is None:
            return HttpResponseRedirect('/login?error=voting requires login&redirect=/s/%s' % key)
        models.Snip.get_snip(key).vote(usr=ac.id, up=(type == 'uv'))
        return HttpResponseRedirect('/s/' + key)
    if type == 't':
        return HttpResponseRedirect('/?tags=%s' % key)
    if type == 'u':
        return HttpResponseRedirect('/?usr=%s' % key)


def index(request):
    c = {'snips': ready_snips(models.Snip.super_filter()[0:10])}
    return render_to_response('filter.html', ready_context(request, c))


def login(request):
    c = csrf(request)

    if request.GET.get('error', False):
        c.update({'error': request.GET['error']})

    if request.session.get('ac', None) is not None:
        c.update({'error': 'logged out'})
        request.session['ac'] = None

    if request.method == 'POST':
        def error(msg):
            c.update({'error': msg})
            return render_to_response('login.html', c)

        def success(ac):
            request.session['ac'] = ac
            return HttpResponseRedirect(request.GET.get('redirect', '/'))

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