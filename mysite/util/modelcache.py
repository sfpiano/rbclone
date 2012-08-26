import hashlib, cPickle as pickle, logging
from django.db.models import signals as db_signals
from django.core.cache import cache

logger = logging.getLogger('caching')
def debug(*args):
    #logger.debug('cache debug {0}'.format(' '.join(args)))
    print 'cache debug {0}'.format(' '.join(args))

md5 = lambda v: hashlib.md5(v).hexdigest()

def ModelCache(model_class, verbose=False, exc_on_not_found=True):
    """
    Returns a callable which will cache the model passed in. See the docstring
    for the returned callable.

    :arg model_class: a django.model.Model class
    :rtype: a callable which can be used to access and cache rows from
    the model class
    """
    def _cacher(q, expiry=60*60*24, using=None):
        """
        This is a cache of %(model)s. You can retrieve single objects using a
        django.models.Q object. The method will cache which exact row is
        identified by this query and cache a it's primary key, in addition to
        the row itself.

        Use it like this::

        from django.contrib.auth.user import User
        from django.models import Q
        from model_cache import ModelCache

        user_cache = ModelCache(User)
        user = user_cache(Q(username='samuraisam', is_active=True)) # woo!
        :arg q: A django `Q` object (to use on `model_class.objects.get()`)
        :arg model_class: A django model class
        :arg expiry: When this key should expire from the cache (in secs)
        :arg using: Tells Django which database to use when quering for the obj
        :rtype: An instance of model_class
        """ % dict(model=model_class.__name__)

        # build an instance of model_class from dict:d
        def _builder(d):
            return pickle.loads(d)
        
        # save an instance of model_class
        def _cache_model(key, obj):
            cache.set(key, pickle.dumps(obj), expiry)
        
        # we save a hash of the query and save it to the pk it actually
        # represents this way we can make cache arbitrary queries that lookup
        # the same object. we also include the model's class name, and
        # a hash of the entire class dictionary (in case the contents change
        # in some way, we'll be prepared)
        mh = md5('{0}{1}{2}'.format(str(q), model_class.__name__,
                                 str(model_class.__dict__)))
        mk = md5('{0}{1}'.format(model_class.__name__, str(model_class.__dict__)))
        pk_key = 'q{0}'.format(mh)
        # see if this query has been performed before
        pk = cache.get(pk_key)
        obj = None
        if pk is not None:
            # HEY WE FOUND A PK FOR THIS QUERY LETS TRY TO GET IT FROM CACHE
            key = 'pk{0}{1}'.format(mk, pk)
            try:
                if verbose:
                    debug('cache hit key', key)
                obj = _builder(cache.get(key))
                obj._from_cache = True
                return obj
            except Exception, e:
                if verbose:
                    debug('cache build error', str(e))
                cache.delete(key)
                cache.delete(pk_key)

        if obj is None:
            # DERP, CACHE MISS
            try:
                obj = model_class._default_manager.using(using).get(q)
            except model_class.DoesNotExist:
                if exc_on_not_found:
                    raise
                else:
                    return None
            # save the query => pk cache
            cache.set(pk_key, str(obj.pk), expiry)
            
            # now we do normal row caching
            key = 'pk{0}{1}'.format(mk, str(obj.pk))
            if verbose:
                debug('cache miss key', key)

            # but don't re-cache if it's not necessary
            if not cache.has_key(key):
                if verbose:
                    debug('caching key', key)
                _cache_model(key, obj)
            obj._from_cache = False
            return obj

    # only connect these things once
    if not hasattr(model_class, '_model_cached'):
        def _clear(sender, instance, *args, **kwargs):
            mk = md5('{0}{1}'.format(model_class.__name__,
                                   str(model_class.__dict__)))
            key = 'pk{0}{1}'.format(mk, str(instance.pk))
            if verbose:
                debug('expiring key', key)
            cache.delete(key)

        db_signals.post_save.connect(_clear, sender=model_class, weak=False)
        db_signals.post_delete.connect(_clear, sender=model_class, weak=False)

        setattr(model_class, '_model_cached', True)
    
    return _cacher
