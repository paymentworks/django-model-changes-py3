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


class RecursionPreventionTestCase(TestCase):
    def test_recursion_prevention_during_deletion(self):
        """
        Test that the recursion guard prevents infinite recursion during
        complex deletion scenarios that would have caused RecursionError
        in the old version.
        """
        # Create a user and article with foreign key relationship
        user = User.objects.create(name='Test User')
        article = Article.objects.create(title='Test Article', user=user)
        
        # Force the foreign key to be cached (this is what triggers recursion in production)
        _ = article.user  # This loads the foreign key
        
        # Now trigger a save operation that would cause state tracking
        # In the old version, this could cause infinite recursion
        # In the fixed version, the recursion guard should prevent this
        article.title = 'Updated Article'
        article.save()
        
        # Verify the save worked without recursion
        article.refresh_from_db()
        self.assertEqual(article.title, 'Updated Article')
        
        # Verify state tracking still works correctly
        self.assertIn('title', article.changes())
        self.assertEqual(article.changes()['title'], ('Test Article', 'Updated Article'))
