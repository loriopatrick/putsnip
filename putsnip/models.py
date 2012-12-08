import base
from django.db import models

#todo: remove possibilities for sql injections in root sql construction methods

class Snip(models.Model):
    """
    Store the code snippet
    PutSnip !!!
    """
    id = models.AutoField(primary_key=True)
    usr = models.CharField(max_length=50)
    title = models.CharField(max_length=100)
    code = models.TextField()
    lan = models.CharField(max_length=30)
    desc = models.TextField(max_length=2048)
    datetime = models.DateTimeField(auto_now_add=True)
    views = models.IntegerField(default=0)

    @staticmethod
    def get_snip_by_points_query (pool='putsnip_snip', nested_pool=False, score='1', order='DESC'):
        """
        sums votes with score of definable value for each snippet
        sorts by score
        """
        if nested_pool:
            pool = '(%s) uniqueTbl' % pool

        if score == '1':
            return '''
            SELECT * FROM %s INNER JOIN (
                SELECT snip, count(*) AS score FROM putsnip_vote
                WHERE up = 1
                GROUP BY snip
                ORDER BY score %s
            ) tbl on tbl.snip = id
            ''' % (pool, order)

        return '''
        SELECT * FROM %s INNER JOIN (
            SELECT snip, sum(%s) AS score FROM putsnip_vote
            WHERE up = 1
            GROUP BY snip
            ORDER BY score %s
        ) tbl on tbl.snip = id
        ''' % (pool, score, order)

    @staticmethod
    def get_trending_score_sql ():
        return '1 / ( UNIX_TIMESTAMP(now()) - UNIX_TIMESTAMP(datetime) )'

    @staticmethod
    def get_trending (pool='putsnip_snip', nested_pool=False, order='DESC'):
        """
        uses score of 1 / age to get trending
        """
        print Snip.get_snip_by_points_query(pool=pool, order=order,
            score=Snip.get_trending_score_sql())

        return Snip.objects.raw(Snip.get_snip_by_points_query(pool=pool, nested_pool=nested_pool, order=order,
            score=Snip.get_trending_score_sql()))

    @staticmethod
    def get_snip (key):
        return Snip.objects.get(id=base.decode(key))

    @staticmethod
    def get_snip_by_tag_query (tags, all=False):
        """
        gets putsnip_tag ids
        gets connections with ids
        gets snips that link with connections
        if all: requires snips to have connections to all tags
        appends order to end of query
        """
        con = ''
        if all:
            con = 'HAVING COUNT(tag) = %s' % len(tags)

        return '''
        SELECT * FROM putsnip_snip WHERE id IN(
            SELECT snip FROM putsnip_tagconnection WHERE tag IN (
                SELECT id FROM putsnip_tag WHERE name IN (%s)
            ) GROUP BY snip %s
        )
        ''' % (('"' + '","'.join(tags) + '"'), con)

    @staticmethod
    def get_snip_by_tags (tags, all=False, order=''):
        """
        executes query from _get_snip_by_tag_query and returns snips
        """
        return Snip.objects.raw(Snip.get_snip_by_tag_query(tags, all) + order)

    @staticmethod
    def super_filter (tags = None, all_tags=False, user='', sort='hot', order='DESC'):
        """
        sort = {hot, views, date, points}
        """
        if tags:
            tag_query = Snip.get_snip_by_tag_query(tags, all_tags)
            if len(user):
                tag_query += ' AND usr="%s"' % user
            if sort == 'hot':
                return Snip.get_trending(tag_query, order)
            if sort == 'points':
                return Snip.objects.raw(Snip.get_snip_by_points_query(pool=tag_query, nested_pool=True, order=order))
            if sort == 'views' or sort == 'date':
                return Snip.objects.raw(tag_query + (' ORDER BY %s %s' % (sort, order)))
        else:
            if sort == 'hot' or sort == 'points':
                con = ''
                if len(user):
                    con = ' WHERE usr="%s"' % user

                score = '1'
                if sort == 'hot':
                    score = Snip.get_trending_score_sql()

                return Snip.objects.raw(Snip.get_snip_by_points_query(score=score, order=order) + con)

            if sort == 'views' or sort == 'date':
                return Snip.objects.raw('SELECT * FROM putsnip_snip ORDER BY %s %s' % (sort, order))

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

    def get_vote (self, usr, force=False):
        if force or not hasattr(self, 'my_vote'):
            vote = Vote.objects.filter(snip=self.id, usr=usr)

            if vote.count() > 0:
                vote = vote[0]
                if vote.up:
                    self.my_vote = 1
                else:
                    self.my_vote = -1
            else:
                self.my_vote = 0
        return self.my_vote

    def vote(self, usr, up=True):
        """
        if exact same vote, remove
        if opposite, update
        if new, add
        """
        vote = Vote.objects.filter(snip=self.id, usr=usr)
        if vote.count() > 0:
            vote = vote.get()
            if vote.up == up:
                vote.delete()
                if up:
                    self.points = self.get_points() - 1
                else:
                    self.points = self.get_points() + 1
                return
            vote.up = up
            vote.save()
            if up:
                self.points = self.get_points() + 2
            else:
                self.points = self.get_points() - 2
            return
        vote = Vote(snip=self.id, usr=usr, up=up)
        vote.save()
        if up:
            self.point = self.get_points() + 1
        else:
            self.point = self.get_points() - 1


    def get_tags (self):
        """
        goes through TagConnections and gets connections with self's snippet id
        finds tags that correspond with found TagConnections
        """
        if not hasattr(self, 'tags_data'):
            self.tags_data = Tag.objects.raw('''SELECT putsnip_tag.* FROM putsnip_tag INNER JOIN( \
                SELECT DISTINCT tag FROM putsnip_tagconnection WHERE snip="%s" \
            ) tbl on tbl.tag = putsnip_tag.id''' % self.id)[0:20]
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
            self.tags = ','.join(r)
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
    points = models.IntegerField(default=-1)


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
            if Tag.objects.filter(name=t).count() > 0:
                tag = Tag.objects.get(name=t)
                if TagConnection.objects.filter(snip=snip, tag=tag.id).count() > 0:
                    return
            else:
                tag.save()

            TagConnection(snip=snip, tag=tag.id).save()



class TagConnection(models.Model):
    snip = models.IntegerField()
    tag = models.IntegerField()