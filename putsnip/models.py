import base
from django.db import models

class Snip(models.Model):
    """
    Store the code snippet
    PutSnip !!!
    """
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    code = models.TextField()
    lan = models.CharField(max_length=30)
    name = models.CharField(max_length=50)
    datetime = models.DateTimeField(auto_now_add=True)
    views = models.IntegerField(default=0)

    @staticmethod
    def get_trending ():
        """
        sums votes with score of 1/age for each snippet
        sorts by score
        """
        return Snip.objects.raw('SELECT putsnip_snip.* FROM putsnip_snip INNER JOIN (\
            SELECT putsnip_vote.snip FROM putsnip_vote GROUP BY snip ORDER BY \
            sum( 1 / (UNIX_TIMESTAMP(now())-UNIX_TIMESTAMP(date))) DESC \
        ) putsnip_vote on putsnip_vote.snip = putsnip_snip.id')

    @staticmethod
    def get_snip (key):
        return Snip.objects.get(id=base.decode(key))

    def get_points(self):
        """
        gets all votes,
        adds upvotes subtracts downvotes,
        return with minimum of 0
        """
        if not hasattr(self, 'points'):
            self.points = max(Vote.objects.filter(snip=self.id, up=True).count() \
                - Vote.objects.filter(snip=self.id, up=False).count(), 0)
        return self.points

    def get_tags (self):
        """
        goes through TagConnections and gets connections with self's snippet id
        finds tags that correspond with found TagConnections
        """
        if not hasattr(self, 'tags_data'):
            self.tags_data = Tag.objects.raw('SELECT putsnip_tag.* FROM putsnip_tag INNER JOIN( \
                SELECT DISTINCT putsnip_tags.tag FROM putsnip_tags WHERE putsnip_tags.snip = "%s" \
            ) putsnip_tags on putsnip_tags.tag = putsnip_tag.id' % self.id)[0:20]
        return self.tags_data

    def get_tags_str (self):
        """
        extracts each tag's name result and
        joins with ',' in str
        """
        if not hasattr(self, 'tags'):
            r = []
            tags = self.get_tags()
            for tag in tags:
                r.append(tag.name)
            self.tags = ','.join(tags)
        return self.tags

    def update_text_numbers (self):
        """
        turns   1,000 into 1k
                1,000,000 into 1M
        """
        def text_num (num):
            temp = round(num / 1000000, 1)
            if temp >= 1:
                return '%iM' % temp
            temp = round(num / 1000, 1)
            if temp >= 1:
                return '%ik' % temp
            return '%i' % num

        self.pointsK = text_num(self.get_points())
        self.viewsK = text_num(self.views)

    def get_key (self):
        """
        adds key to self, which is a base ~64 version of id
        """
        if not hasattr(self, 'key'):
            self.key = base.encode(self.id)
        return self.key

    def add_view (self, amt=1):
        self.views += amt
        self.save()


class Account(models.Model):
    id = models.AutoField(primary_key=True)
    usr = models.CharField(max_length=20, null=False, unique=True)
    email = models.CharField(max_length=255)
    pwd = models.CharField(max_length=32, null=False)
    datetime = models.DateTimeField(auto_now_add=True)
    points = models.IntegerField(default=0)


class Vote(models.Model):
    snip = models.IntegerField()
    usr = models.IntegerField()
    up = models.BooleanField(default=True)
    datetime = models.DateTimeField(auto_now_add=True)


class Tag(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)

    @staticmethod
    def add_tags (snip, tags):
        """
        adds tags to pool if new
        creates connections between snip and tags
        """
        if isinstance(tags, str):
            tags = tags.split(',')
        for t in tags:
            tag = Tag(name=t)
            if tag.objects.count() > 0:
                tag.objects.get()
                if TagConnection(snip=snip, tag=tag.id).objects.count() > 0:
                    return
            else:
                tag.save()

            TagConnection(snip=snip, tag=tag.id).save()



class TagConnection(models.Model):
    snip = models.IntegerField()
    tag = models.IntegerField()

    def get_snip(self):
        return Snip(id=self.snip).objects.get()

    def get_tag(self):
        return Tag(id=self.tag).objects.all()