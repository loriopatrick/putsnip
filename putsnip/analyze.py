from models import Snip, Tag


def compute_trending_tags ():
    res = Snip.objects.raw('SELECT * FROM ')

def get_trending_snips ():
    return Snip.objects.raw('SELECT putsnip_snip.* FROM putsnip_snip INNER JOIN (\
        SELECT putsnip_vote.snip FROM putsnip_vote GROUP BY snip ORDER BY \
        sum( 1 / (UNIX_TIMESTAMP(now())-UNIX_TIMESTAMP(date))) DESC \
    ) putsnip_vote on putsnip_vote.snip = putsnip_snip.id')