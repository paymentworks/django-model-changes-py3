import gc
import weakref

from django.db.models import signals
from django.test import TestCase

from .models import User, Article


class ChangesMixinBeforeAndCurrentTestCase(TestCase):
    def test_empty(self):
        user = User()

        self.assertDictContainsSubset({'id': None, 'name': ''}, user.old_state())
        self.assertDictContainsSubset({'id': None, 'name': ''}, user.previous_state())
        self.assertDictContainsSubset({'id': None, 'name': ''}, user.current_state())
        self.assertEqual({}, user.old_changes())
        self.assertEqual({}, user.changes())

    def test_new(self):
        user = User(name='Foo Bar')

        self.assertDictContainsSubset({'id': None, 'name': 'Foo Bar'}, user.old_state())
        self.assertDictContainsSubset({'id': None, 'name': 'Foo Bar'}, user.previous_state())
        self.assertDictContainsSubset({'id': None, 'name': 'Foo Bar'}, user.current_state())
        self.assertEqual({}, user.old_changes())
        self.assertEqual({}, user.changes())

    def test_change_from_new(self):
        user = User()
        user.name = 'Foo Bar'

        self.assertDictContainsSubset({'id': None, 'name': ''}, user.old_state())
        self.assertDictContainsSubset({'id': None, 'name': ''}, user.previous_state())
        self.assertDictContainsSubset({'id': None, 'name': 'Foo Bar'}, user.current_state())
        self.assertEqual({'name': ('', 'Foo Bar')}, user.old_changes())
        self.assertEqual({'name': ('', 'Foo Bar')}, user.changes())

    def test_change_from_db(self):
        user = User(name='Foo Bar')
        user.save()

        self.assertDictContainsSubset({'id': None, 'name': 'Foo Bar'}, user.old_state())
        self.assertDictContainsSubset({'id': 1, 'name': 'Foo Bar'}, user.previous_state())
        self.assertDictContainsSubset({'id': 1, 'name': 'Foo Bar'}, user.current_state())

        user = User.objects.filter(pk=user.pk)[0]
        user.name = 'My Real Name'

        self.assertDictContainsSubset({'id': 1, 'name': 'Foo Bar'}, user.old_state())
        self.assertDictContainsSubset({'id': 1, 'name': 'Foo Bar'}, user.previous_state())
        self.assertDictContainsSubset({'id': 1, 'name': 'My Real Name'}, user.current_state())
        self.assertEqual({'name': ('Foo Bar', 'My Real Name')}, user.old_changes())

    def test_save(self):
        user = User()
        user.name = 'Foo Bar'
        user.save()

        user.name = 'My Real Name'

        pk = user.pk

        self.assertDictContainsSubset({'id': None, 'name': ''}, user.old_state())
        self.assertDictContainsSubset({'id': pk, 'name': 'Foo Bar'}, user.previous_state())
        self.assertDictContainsSubset({'id': pk, 'name': 'My Real Name'}, user.current_state())
        self.assertDictEqual({'id': (None, pk), 'name': ('', 'My Real Name')}, user.old_changes())
        self.assertFalse(user.was_persisted())
        self.assertTrue(user.is_persisted())

        user.save()

        self.assertDictContainsSubset({'id': pk, 'name': 'Foo Bar'}, user.old_state())
        self.assertDictContainsSubset({'id': pk, 'name': 'My Real Name'}, user.previous_state())
        self.assertDictContainsSubset({'id': pk, 'name': 'My Real Name'}, user.current_state())
        self.assertEqual({'name': ('Foo Bar', 'My Real Name')}, user.old_changes())
        self.assertTrue(user.was_persisted())
        self.assertTrue(user.is_persisted())


        user.name = 'I Changed My Mind'
        user.save()

        self.assertDictContainsSubset({'id': pk, 'name': 'My Real Name'}, user.old_state())
        self.assertDictContainsSubset({'id': pk, 'name': 'I Changed My Mind'}, user.current_state())
        self.assertEqual({'name': ('My Real Name', 'I Changed My Mind')}, user.old_changes())
        self.assertTrue(user.was_persisted())
        self.assertTrue(user.is_persisted())


    def test_new_is_was_persisted(self):
        user = User()
        self.assertFalse(user.was_persisted())
        self.assertFalse(user.is_persisted())

        user.save()
        self.assertFalse(user.was_persisted())
        self.assertTrue(user.is_persisted())

        user.delete()
        self.assertTrue(user.was_persisted())
        self.assertFalse(user.is_persisted())

        user.save()
        self.assertFalse(user.was_persisted())
        self.assertTrue(user.is_persisted())

        user.delete()
        self.assertTrue(user.was_persisted())
        self.assertFalse(user.is_persisted())

    def test_foreign_key(self):
        me = User()
        me.save()

        you = User()
        you.save()

        article = Article(title='Hello World', user=me)

        self.assertDictContainsSubset({'id': None, 'user': me}, article.old_state())
        self.assertDictContainsSubset({'id': None, 'user': me}, article.previous_state())
        self.assertDictContainsSubset({'id': None, 'user': me}, article.current_state())

        article.save()

        self.assertDictContainsSubset({'id': None, 'user': me}, article.old_state())
        self.assertDictContainsSubset({'id': article.pk, 'user': me}, article.previous_state())
        self.assertDictContainsSubset({'id': article.pk, 'user': me}, article.current_state())

        article.user = you

        self.assertDictContainsSubset({'id': None, 'user': me}, article.old_state())
        self.assertDictContainsSubset({'id': article.pk, 'user': me}, article.previous_state())
        self.assertDictContainsSubset({'id': article.pk, 'user': you}, article.current_state())

        article.save()

        self.assertDictContainsSubset({'id': article.pk, 'user': me}, article.old_state())
        self.assertDictContainsSubset({'id': article.pk, 'user': you}, article.previous_state())
        self.assertDictContainsSubset({'id': article.pk, 'user': you}, article.current_state())


    def test_foreign_key_model_in_previous_state_but_not_current_state(self):
        """
        GIVEN a user and article
        WHEN the article's foreign key ID is updated and the model is refreshed
            from the database
        THEN the current state should *not* have the user model in its state because
            it isn't in the model's field cache and therefore, the changes should only
            show the ID change.
        """
        user = User.objects.create()
        user2 = User.objects.create()
        article = Article.objects.create(title='Hello World', user=user)

        Article.objects.filter(id=article.id).update(user_id=user2.pk)
        article.refresh_from_db()

        self.assertDictEqual({'id': None, 'title': 'Hello World', 'user_id': user.id, 'user': user}, article.old_state())
        self.assertDictEqual({'id': article.pk, 'title': 'Hello World', 'user_id': user.id, 'user': user}, article.previous_state())
        self.assertDictEqual({'id': article.pk, 'title': 'Hello World', 'user_id': user2.pk}, article.current_state())
        self.assertDictEqual({'user_id': (user.id, user2.pk)}, article.changes())

    def test_foreign_key_id(self):
        me = User()
        me.save()

        you = User()
        you.save()

        article = Article(title='Hello World', user_id=me.id)

        self.assertDictContainsSubset({'id': None, 'user_id': me.pk}, article.old_state())
        self.assertDictContainsSubset({'id': None, 'user_id': me.pk}, article.previous_state())
        self.assertDictContainsSubset({'id': None, 'user_id': me.pk}, article.current_state())

        article.save()

        self.assertDictContainsSubset({'id': None, 'user_id': me.pk}, article.old_state())
        self.assertDictContainsSubset({'id': article.pk, 'user_id': me.pk}, article.previous_state())
        self.assertDictContainsSubset({'id': article.pk, 'user_id': me.pk}, article.current_state())

        article.user = you

        self.assertDictContainsSubset({'id': None, 'user_id': me.pk}, article.old_state())
        self.assertDictContainsSubset({'id': article.pk, 'user_id': me.pk}, article.previous_state())
        self.assertDictContainsSubset({'id': article.pk, 'user_id': you.pk}, article.current_state())

        article.save()

        self.assertDictContainsSubset({'id': article.pk, 'user_id': me.pk}, article.old_state())
        self.assertDictContainsSubset({'id': article.pk, 'user_id': you.pk}, article.previous_state())
        self.assertDictContainsSubset({'id': article.pk, 'user_id': you.pk}, article.current_state())


    def test_deferred_fields_no_infinite_recursion(self):
        user = User()
        user.save()
        User.objects.only('id').get(id=user.id)


class ChangesMixinDoesNotLeakFinalizersTestCase(TestCase):
    """
    ChangesMixin.__init__ connects post_save/post_delete on every instantiation.

    Django's Signal.connect() registers a weakref.finalize() before it checks
    dispatch_uid, and finalize() entries are held in a global registry until the
    caller dies.

    The receivers are functions that outlive the interpreter, so a weak connect leaks registry entries.
     
    Connecting with weak=False avoids the finalize() call entirely, and no leak occurs.
    """

    def test_instantiation_does_not_grow_the_finalize_registry(self):
        # Warm up so any one-time setup is not counted below.
        for _ in range(10):
            User()

        gc.collect()
        before = len(weakref.finalize._registry)

        for _ in range(500):
            User()

        gc.collect()
        growth = len(weakref.finalize._registry) - before

        self.assertEqual(
            growth, 0,
            'Instantiating 500 models added %d weakref.finalize entries that will '
            'never be evicted. ChangesMixin must connect its signals with '
            'weak=False.' % growth
        )

    def test_receivers_are_still_connected_exactly_once(self):
        # The leak fix must not change dispatch behaviour: dispatch_uid should
        # still collapse every instantiation down to a single receiver per model.
        def uids(signal):
            return [key for key, _ in signal.receivers
                    if key[0] == 'django-changes-User']

        for _ in range(50):
            User()

        self.assertEqual(len(uids(signals.post_save)), 1)
        self.assertEqual(len(uids(signals.post_delete)), 1)

    def test_post_save_receiver_still_fires(self):
        # weak=False stores a strong reference to the receiver rather than a
        # weakref, so prove the receiver is still reachable and still updates
        # state on save.
        user = User(name='Foo')
        user.save()

        user.name = 'Bar'
        self.assertEqual({'name': ('Foo', 'Bar')}, user.changes())

        user.save()
        self.assertEqual({}, user.changes())
        self.assertEqual({'name': ('Foo', 'Bar')}, user.previous_changes())
